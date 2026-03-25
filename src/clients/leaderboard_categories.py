from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LeaderboardCategories:
    """Работа с категориями лидерборда HackerOne"""

    CATEGORIES = {
        "reputation": "/leaderboard",
        "high_critical": "/leaderboard/high_critical",
        "owasp": "/leaderboard/owasp",
        "country": "/leaderboard/country",
        "asset_type": "/leaderboard/asset_type",
        "up_and_comers": "/leaderboard/up_and_comers",
        "upvotes": "/leaderboard/upvotes"
    }

    def __init__(self, scraper):
        self.scraper = scraper
        self.driver = scraper.driver

    def open_category(self, category: str):
        """Открыть конкретную категорию лидерборда"""
        url = self.CATEGORIES.get(category, self.CATEGORIES["reputation"])
        full_url = f"{self.scraper.base_url}{url}"
        self.driver.get(full_url)
        self.scraper._wait_for_content()

    def get_available_categories(self):
        """Получить доступные категории со страницы"""
        categories = []
        tabs = self.driver.find_elements(By.CSS_SELECTOR, '[role="tab"]')
        for tab in tabs:
            categories.append(tab.text)
        return categories