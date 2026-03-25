import base64
import logging
import time
from typing import Optional, Dict, List
from datetime import datetime
import requests
from pathlib import Path
import yaml
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

load_dotenv()


class HackerOneAPIClient:
    """
    Официальный клиент HackerOne API
    Документация: https://api.hackerone.com/
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.base_url = self.config['hackerone']['api']['base_url']
        self.version = self.config['hackerone']['api']['version']
        self.timeout = self.config['hackerone']['api']['timeout']
        self.rate_limit = self.config['hackerone']['api']['rate_limit']

        # API Credentials
        self.api_token = os.getenv('HACKERONE_API_TOKEN')
        self.api_secret = os.getenv('HACKERONE_API_SECRET')
        self.username = os.getenv('HACKERONE_USERNAME')

        self.session = requests.Session()
        self._last_request_time = 0
        self._request_count = 0

        # Настройка аутентификации
        if self.api_token and self.api_secret:
            credentials = f"{self.api_token}:{self.api_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()
            self.session.headers.update({
                'Authorization': f'Basic {encoded}',
                'Accept': 'application/json',
                'User-Agent': 'HackerOneResearch/1.0'
            })
            logger.info("✓ API аутентификация настроена")
        else:
            logger.warning("⚠ API ключи не найдены — режим ограниченного доступа")

        logger.info("✓ HackerOneAPIClient инициализирован")

    def _load_config(self, config_path: Optional[Path] = None) -> Dict:
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'config.yaml'

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

        # Конфиг по умолчанию
        return {
            'hackerone': {
                'api': {
                    'base_url': 'https://api.hackerone.com',
                    'version': 'v1',
                    'timeout': 30,
                    'rate_limit': {'requests_per_minute': 600, 'delay_between_requests': 0.1}
                },
                'scraper': {
                    'base_url': 'https://hackerone.com',
                    'delay_between_requests': 2.0,
                    'max_retries': 3
                }
            },
            'data': {
                'limit': {'hackers': 50, 'reports': 100, 'profiles': 10},
                'export': {'formats': ['json', 'csv'], 'output_dir': 'data/processed'}
            }
        }

    def _rate_limit(self):
        """Соблюдение rate limit API"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        min_delay = 60 / self.rate_limit['requests_per_minute']

        if time_since_last < min_delay:
            time.sleep(min_delay - time_since_last)

        self._last_request_time = time.time()
        self._request_count += 1

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Выполнить API запрос"""
        url = f"{self.base_url}/{self.version}/{endpoint}"

        for attempt in range(3):
            try:
                self._rate_limit()

                response = self.session.get(url, params=params, timeout=self.timeout)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.error("❌ Ошибка аутентификации (401)")
                    return None
                elif response.status_code == 403:
                    logger.error("❌ Доступ запрещён (403)")
                    return None
                elif response.status_code == 429:
                    logger.warning("⚠ Rate limit hit, waiting 60s...")
                    time.sleep(60)
                elif response.status_code == 404:
                    logger.warning(f"⚠ Ресурс не найден: {endpoint}")
                    return None
                else:
                    logger.warning(f"⚠ Статус {response.status_code}, попытка {attempt + 1}")
                    time.sleep(5)

            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Ошибка запроса: {e}")
                if attempt < 2:
                    time.sleep(5)
                else:
                    return None

        return None

    def get_my_reports(self, limit: int = 100) -> List[Dict]:
        """Получить МОИ отчёты (требует API токена хакера)"""
        logger.info(f"📊 Запрос моих отчётов: {limit}")

        if not self.api_token:
            logger.warning("⚠ API токен не настроен — возвращаем пустой список")
            return []

        data = self._make_request('hackers/reports', {
            'page[size]': min(limit, 100),
            'sort': '-created_at'
        })

        if data and 'data' in data:
            logger.info(f"✓ Получено {len(data['data'])} отчётов")
            return data['data']

        return []

    def get_my_programs(self) -> List[Dict]:
        """Получить программы, в которых я участвую"""
        logger.info("📊 Запрос моих программ")

        if not self.api_token:
            return []

        data = self._make_request('hackers/programs')

        if data and 'data' in data:
            logger.info(f"✓ Получено {len(data['data'])} программ")
            return data['data']

        return []

    def get_hacktivity(self, limit: int = 50) -> List[Dict]:
        """Получить публичные отчёты из Hacktivity"""
        logger.info(f"📰 Запрос hacktivity: {limit}")

        data = self._make_request('hacktivity', {
            'page[size]': min(limit, 100),
            'range[type]': 'disclosed_at',
            'range[start]': (datetime.now().replace(day=1)).strftime('%Y-%m-%d')
        })

        if data and 'data' in data:
            logger.info(f"✓ Получено {len(data['data'])} отчётов из hacktivity")
            return data['data']

        return []

    def get_program_details(self, program_id: str) -> Optional[Dict]:
        """Получить детали программы"""
        logger.info(f"📊 Запрос программы: {program_id}")
        data = self._make_request(f'programs/{program_id}')
        return data.get('data') if data else None

    def close(self):
        self.session.close()
        logger.info(f"📊 Всего API запросов: {self._request_count}")