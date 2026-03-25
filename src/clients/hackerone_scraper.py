import logging
import time
import random
from typing import Optional, Dict, List, Set
from datetime import datetime
from pathlib import Path
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HackerOneScraper:
    CATEGORIES = {
        "reputation": "/leaderboard",
        "high_critical": "/leaderboard/high_critical",
        "owasp": "/leaderboard/owasp",
        "country": "/leaderboard/country",
        "asset_type": "/leaderboard/asset_type",
        "up_and_comers": "/leaderboard/up_and_comers",
        "upvotes": "/leaderboard/upvotes"
    }

    def __init__(self, config_path: Optional[Path] = None, headless: bool = True):
        self.config = self._load_config(config_path)
        self.base_url = self.config.get('hackerone', {}).get('scraper', {}).get('base_url', 'https://hackerone.com')
        self.delay = self.config.get('hackerone', {}).get('scraper', {}).get('delay_between_requests', 2.0)
        self.max_retries = self.config.get('hackerone', {}).get('scraper', {}).get('max_retries', 3)
        self.headless = headless
        self.driver = None
        self._request_count = 0
        self.debug_dir = Path(__file__).parent.parent.parent / 'data' / 'debug'
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self._init_browser()
        logger.info("Chrome WebDriver инициализирован")

    def _load_config(self, config_path: Optional[Path] = None) -> Dict:
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception:
                pass
        return {
            'hackerone': {
                'scraper': {
                    'base_url': 'https://hackerone.com',
                    'delay_between_requests': 2.0,
                    'max_retries': 3
                }
            }
        }

    def _init_browser(self):
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
            logger.info(f"Браузер запущен (headless={self.headless})")
        except Exception as e:
            logger.error(f"Ошибка инициализации браузера: {e}")
            raise

    def _rate_limit(self):
        time.sleep(self.delay + random.uniform(0.5, 2.0))
        self._request_count += 1
        if self._request_count % 10 == 0:
            logger.info(f"Выполнено запросов: {self._request_count}")

    def _wait_for_content(self, timeout: int = 30):
        time.sleep(5)
        for scroll_num in range(5):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            logger.debug(f"Прокрутка {scroll_num + 1}/5 завершена")
        for i in range(timeout):
            time.sleep(1)
            rows = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid^="table-row-"]')
            if len(rows) >= 10:
                logger.debug(f"Найдено {len(rows)} строк таблицы")
                break
        logger.info(f"Контент загружен за {i + 1} сек")

    def _save_debug_html(self, filename: str):
        try:
            html = self.driver.page_source
            filepath = self.debug_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"HTML сохранён: {filepath}")
        except Exception as e:
            logger.error(f"Не удалось сохранить HTML: {e}")

    def open_category(self, category: str):
        url_path = self.CATEGORIES.get(category, self.CATEGORIES["reputation"])
        url = f"{self.base_url}{url_path}"
        logger.info(f"Открываем категорию: {category} -> {url}")
        self.driver.get(url)
        self._rate_limit()
        self._wait_for_content(30)

    def get_available_categories(self) -> List[str]:
        try:
            self.driver.get(f"{self.base_url}/leaderboard")
            time.sleep(3)
            tabs = self.driver.find_elements(By.CSS_SELECTOR, '[role="tab"]')
            categories = [tab.text.strip().lower() for tab in tabs if tab.text.strip()]
            return categories if categories else list(self.CATEGORIES.keys())
        except Exception as e:
            logger.warning(f"Не удалось получить категории: {e}")
            return list(self.CATEGORIES.keys())

    def fetch_leaderboard(self, limit: int = 50, category: str = "reputation") -> List[Dict]:
        logger.info(f"Сбор лидерборда: {limit} хакеров, категория: {category}")
        hackers = []
        seen_usernames: Set[str] = set()
        excluded = {'leaderboard', 'hacktivity', 'opportunities', 'directory', 'programs', 'users', 'settings', 'login', 'signup', 'security'}

        try:
            self.open_category(category)
            self._save_debug_html(f'leaderboard_{category}_debug.html')
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            table_rows = soup.find_all('div', {'role': 'row', 'data-testid': lambda x: x and 'table-row-' in x and 'Z2lk' in x})
            logger.debug(f"Найдено строк таблицы: {len(table_rows)}")

            for row in table_rows:
                if len(hackers) >= limit:
                    break
                hacker_data = self._parse_leaderboard_row(row, seen_usernames, excluded)
                if hacker_data:
                    username = hacker_data['username']
                    if username and username not in seen_usernames:
                        seen_usernames.add(username)
                        hackers.append(hacker_data)
                        logger.debug(f"Найден хакер: {username} (rep: {hacker_data['reputation']}, signal: {hacker_data['signal']}, impact: {hacker_data['impact']})")

            logger.info(f"Собрано {len(hackers)} уникальных профилей из лидерборда")
        except Exception as e:
            logger.error(f"Ошибка сбора лидерборда: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return hackers[:limit]

    def _parse_leaderboard_row(self, row, seen_usernames: Set[str], excluded: Set[str]) -> Optional[Dict]:
        try:
            cells = row.find_all('div', {'role': 'cell'})
            if len(cells) < 4:
                return None
            username_cell = cells[0]
            link = username_cell.find('a', href=True)
            if not link:
                return None
            href = link.get('href', '')
            username = link.get_text(strip=True)
            if not username and href.startswith('/'):
                username = href.lstrip('/').split('?')[0]
            if not username or len(username) < 3:
                return None
            if username in excluded or username in seen_usernames:
                return None

            reputation = 0
            if len(cells) > 1:
                rep_cell = cells[1].find('div', {'class': 'TableCell-module_u1-table__cell-inner-container__8-nd1'})
                if not rep_cell:
                    rep_cell = cells[1]
                rep_text = rep_cell.get_text(strip=True)
                reputation = int(''.join(filter(str.isdigit, rep_text)) or 0)

            signal = 0.0
            if len(cells) > 2:
                signal_cell = cells[2].find('div', {'class': 'TableCell-module_u1-table__cell-inner-container__8-nd1'})
                if not signal_cell:
                    signal_cell = cells[2]
                signal_text = signal_cell.get_text(strip=True)
                signal = float(''.join(filter(lambda x: x.isdigit() or x == '.', signal_text)) or 0)
                signal = signal * 10

            impact = 0.0
            if len(cells) > 3:
                impact_cell = cells[3].find('div', {'class': 'TableCell-module_u1-table__cell-inner-container__8-nd1'})
                if not impact_cell:
                    impact_cell = cells[3]
                impact_text = impact_cell.get_text(strip=True)
                impact = float(''.join(filter(lambda x: x.isdigit() or x == '.', impact_text)) or 0)
                impact = int(impact * 1000)

            return {
                'username': username,
                'rank': len(seen_usernames) + 1,
                'reputation': reputation,
                'signal': signal,
                'impact': impact,
                'country': None,
                'is_verified': reputation > 5000,
                'total_bounties': 0.0,
                'total_reports': 0,
                'accepted_reports': 0,
                'skills': [],
                'profile_url': f"{self.base_url}/{username}"
            }
        except Exception as e:
            logger.debug(f"Ошибка парсинга строки: {e}")
            return None

    def fetch_hacktivity(self, limit: int = 50) -> List[Dict]:
        logger.info(f"Сбор hacktivity: {limit} отчётов")
        reports = []
        seen_ids: Set[int] = set()
        try:
            url = f"{self.base_url}/hacktivity"
            logger.info(f"Открываем: {url}")
            self.driver.get(url)
            self._rate_limit()
            self._wait_for_content(30)
            self._save_debug_html('hacktivity_debug.html')
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            all_links = soup.find_all('a', href=True)

            for link in all_links:
                if len(reports) >= limit:
                    break
                href = link.get('href', '')
                title = link.get('title', link.get_text(strip=True)[:200])
                if '/reports/' in href:
                    try:
                        report_id = int(''.join(filter(str.isdigit, href.split('/reports/')[-1])) or 0)
                        if report_id and report_id not in seen_ids:
                            seen_ids.add(report_id)
                            parent_row = link.find_parent('div', {'role': 'row'})
                            hacker = ''
                            program = ''
                            if parent_row:
                                cells = parent_row.find_all('div', {'role': 'cell'})
                                if len(cells) >= 3:
                                    hacker_cell = cells[1].find('a', href=True)
                                    if hacker_cell:
                                        hacker = hacker_cell.get_text(strip=True).lstrip('@')
                                    if len(cells) > 2:
                                        program = cells[2].get_text(strip=True)
                            reports.append({
                                'report_id': report_id,
                                'title': title if title else f"Report_{report_id}",
                                'state': 'resolved',
                                'hacker_username': hacker,
                                'program_name': program,
                                'bounty_amount': 0.0,
                                'severity': None
                            })
                    except Exception:
                        continue

            if len(reports) < limit:
                logger.info("Пробуем альтернативный метод парсинга hacktivity...")
                reports.extend(self._parse_hacktivity_alternative(soup, limit - len(reports)))

            logger.info(f"Собрано {len(reports)} отчётов из hacktivity")
        except Exception as e:
            logger.error(f"Ошибка сбора hacktivity: {e}")
            import traceback
            logger.error(traceback.format_exc())
        return reports[:limit]

    def _parse_hacktivity_alternative(self, soup, limit: int) -> List[Dict]:
        reports = []
        report_id_counter = 300000
        selectors = ['[class*="report"]', '[class*="disclosure"]', '[class*="hacktivity"]', 'article', 'div[class*="card"]']
        for selector in selectors:
            if len(reports) >= limit:
                break
            try:
                elements = soup.select(selector)
                for elem in elements:
                    if len(reports) >= limit:
                        break
                    title = elem.get_text(strip=True)[:150]
                    if title and len(title) > 10 and 'report' not in title.lower():
                        report_id_counter += 1
                        reports.append({
                            'report_id': report_id_counter,
                            'title': title,
                            'state': 'resolved',
                            'hacker_username': '',
                            'program_name': '',
                            'bounty_amount': 0.0,
                            'severity': None
                        })
            except Exception:
                continue
        return reports

    def fetch_profile(self, username: str) -> Dict:
        logger.info(f"Сбор профиля: {username}")
        url = f"{self.base_url}/{username}"
        try:
            self.driver.get(url)
            self._rate_limit()
            time.sleep(5)
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            profile_data = {
                'username': username,
                'reputation': 0,
                'signal': 0.0,
                'is_verified': False,
                'total_reports': 0,
                'accepted_reports': 0,
                'impact': 0,
                'total_bounties': 0.0,
                'country': None,
                'skills': []
            }
            stat_patterns = [
                {'class': lambda x: x and 'reputation' in str(x).lower()},
                {'data-testid': lambda x: x and 'reputation' in str(x).lower()},
                {'class': lambda x: x and 'stat' in str(x).lower()},
            ]
            for pattern in stat_patterns:
                elems = soup.find_all(**pattern)
                for elem in elems:
                    text = elem.get_text(strip=True)
                    nums = ''.join(filter(str.isdigit, text))
                    if nums and len(nums) >= 3:
                        if 'reputation' in str(elem).lower() or 'rep' in text.lower():
                            profile_data['reputation'] = int(nums)
            signal_elem = soup.find(string=lambda x: x and 'signal' in str(x).lower())
            if signal_elem:
                parent = signal_elem.find_parent()
                if parent:
                    text = parent.get_text(strip=True)
                    nums = ''.join(filter(lambda c: c.isdigit() or c == '.', text))
                    if nums:
                        profile_data['signal'] = float(nums)
            profile_data['is_verified'] = bool(soup.find(class_=lambda x: x and 'verified' in str(x).lower()))
            country_elem = soup.find(class_=lambda x: x and 'country' in str(x).lower())
            if country_elem:
                profile_data['country'] = country_elem.get('title', country_elem.get_text(strip=True))
            skills_elems = soup.find_all(class_=lambda x: x and ('skill' in str(x).lower() or 'tag' in str(x).lower()))
            profile_data['skills'] = [s.get_text(strip=True) for s in skills_elems[:10] if s.get_text(strip=True)]
            logger.info(f"Профиль {username} собран")
            return profile_data
        except Exception as e:
            logger.error(f"Ошибка сбора профиля {username}: {e}")
            return {}

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        logger.info(f"Всего выполнено запросов: {self._request_count}")