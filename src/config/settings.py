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
    reputation: float = 0.25
    signal: float = 0.20
    impact: float = 0.20
    acceptance_rate: float = 0.20
    activity_recency: float = 0.15

    def __post_init__(self):
        total = self.reputation + self.signal + self.impact + self.acceptance_rate + self.activity_recency
        if abs(total - 1.0) > 0.01:
            self.reputation = self.reputation / total
            self.signal = self.signal / total
            self.impact = self.impact / total
            self.acceptance_rate = self.acceptance_rate / total
            self.activity_recency = self.activity_recency / total


@dataclass
class AdvancedMetricsWeights:
    """Расширенные веса для улучшенной формулы рейтинга"""
    base_reputation: float = 0.15
    normalized_signal: float = 0.15
    impact_score: float = 0.15
    report_quality: float = 0.20
    consistency_bonus: float = 0.15
    recency_factor: float = 0.10
    verification_bonus: float = 0.10

    def __post_init__(self):
        total = (self.base_reputation + self.normalized_signal + self.impact_score +
                 self.report_quality + self.consistency_bonus + self.recency_factor +
                 self.verification_bonus)
        if abs(total - 1.0) > 0.01:
            self.base_reputation /= total
            self.normalized_signal /= total
            self.impact_score /= total
            self.report_quality /= total
            self.consistency_bonus /= total
            self.recency_factor /= total
            self.verification_bonus /= total


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
    default_category: str = "reputation"


@dataclass
class InterfaceConfig:
    """Конфигурация интерфейса"""
    default_limit: int = 20
    default_reports: int = 30
    default_headless: bool = True
    default_export_formats: tuple = ("json", "csv")
    max_concurrent_requests: int = 5
    show_progress_bar: bool = True
    auto_save_logs: bool = True


@dataclass
class ExportConfig:
    """Конфигурация экспорта"""
    include_profile_links: bool = True
    excel_auto_width: bool = True
    excel_max_column_width: int = 50
    csv_delimiter: str = ","
    json_indent: int = 2
    json_ensure_ascii: bool = False


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
    advanced_metrics_weights: AdvancedMetricsWeights = field(default_factory=AdvancedMetricsWeights)
    tier_thresholds: TierThresholds = field(default_factory=TierThresholds)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    interface: InterfaceConfig = field(default_factory=InterfaceConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

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
                advanced_metrics_weights=AdvancedMetricsWeights(
                    **config_data.get('analysis', {}).get('advanced_metrics_weights', {})
                ),
                tier_thresholds=TierThresholds(
                    **config_data.get('analysis', {}).get('tier_thresholds', {})
                ),
                interface=InterfaceConfig(
                    **config_data.get('interface', {})
                ),
                export=ExportConfig(
                    **config_data.get('export', {})
                )
            )
        return cls()