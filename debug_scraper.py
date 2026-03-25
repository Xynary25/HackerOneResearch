#!/usr/bin/env python3
"""Скрипт для отладки парсинга HackerOne"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


def debug_hackerone():
    print("🔍 Отладка HackerOne...")

    # Создаём директорию debug
    debug_dir = Path(__file__).parent / 'data' / 'debug'
    debug_dir.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print("🌐 Открываем hackerone.com/leaderboard...")
        driver.get('https://hackerone.com/leaderboard')
        time.sleep(10)

        html = driver.page_source
        print(f"📄 Длина HTML: {len(html)} символов")

        soup = BeautifulSoup(html, 'lxml')

        # Все ссылки
        links = soup.find_all('a', href=True)
        print(f"🔗 Всего ссылок: {len(links)}")

        # Ссылки на профили хакеров
        excluded = {'hacktivity', 'leaderboard', 'opportunities', 'directory', 'programs', 'login'}
        hackers = []

        for i, link in enumerate(links[:100]):
            href = link.get('href', '')
            text = link.get_text(strip=True)[:50]

            # Паттерн для ссылок на профили
            if href.startswith('/') and href.count('/') == 1:
                username = href.lstrip('/').split('?')[0]
                if username and username not in excluded and len(username) >= 3:
                    hackers.append(username)
                    print(f"  [{i}] {href} -> {username}")

        print(f"\n✓ Найдено уникальных хакеров: {len(set(hackers))}")

        # Сохраняем HTML
        filepath = debug_dir / 'debug_leaderboard.html'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"📁 HTML сохранён в {filepath}")

    finally:
        driver.quit()


if __name__ == '__main__':
    debug_hackerone()