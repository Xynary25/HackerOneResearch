from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path
import yaml


@dataclass
class RateLimitConfig:
    """Конфигурация rate limiting"""
    requests_per_minute: int = 30
    delay_between_requests: float = 2.0
    max_retries: int = 3
    timeout: int = 30


@dataclass
class MetricsWeights:
    """Веса метрик для расчёта value_score"""
    reputation: float = 0.40
    signal: float = 0.30
    impact: float = 0.30

    def __post_init__(self):
        total = self.reputation + self.signal + self.impact
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Сумма весов должна быть 1.0, сейчас: {total}")


@dataclass
class TierThresholds:
    """Пороги для определения tier хакера"""
    elite: int = 80
    premium: int = 60
    standard: int = 40


@dataclass
class ScraperConfig:
    """Конфигурация скрапера"""
    base_url: str = "https://hackerone.com"
    leaderboard_url: str = "https://hackerone.com/leaderboard"
    hacktivity_url: str = "https://hackerone.com/hacktivity"
    scroll_iterations: int = 5
    wait_timeout: int = 30


@dataclass
class AppConfig:
    """Основная конфигурация приложения"""
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")

    processed_data_dir: str = "processed"
    debug_data_dir: str = "debug"

    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    metrics_weights: MetricsWeights = field(default_factory=MetricsWeights)
    tier_thresholds: TierThresholds = field(default_factory=TierThresholds)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)

    def __post_init__(self):
        """Создание необходимых директорий"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / self.processed_data_dir).mkdir(exist_ok=True)
        (self.data_dir / self.debug_data_dir).mkdir(exist_ok=True)

    @classmethod
    def from_yaml(cls, config_path: Path) -> 'AppConfig':
        """Загрузка конфигурации из YAML файла"""
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            return cls(
                rate_limit=RateLimitConfig(
                    **config_data.get('hackerone', {}).get('api', {}).get('rate_limit', {})
                ),
                scraper=ScraperConfig(
                    **config_data.get('hackerone', {}).get('scraper', {})
                ),
                metrics_weights=MetricsWeights(
                    **config_data.get('analysis', {}).get('metrics_weights', {})
                ),
                tier_thresholds=TierThresholds(
                    **config_data.get('analysis', {}).get('tier_thresholds', {})
                )
            )
        return cls()