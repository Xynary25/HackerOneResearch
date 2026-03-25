from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import yaml


@dataclass
class RateLimitConfig:
    requests_per_minute: int = 30
    delay_between_requests: float = 2.0
    max_retries: int = 3
    timeout: int = 30


@dataclass
class MetricsWeights:
    reputation: float = 0.40
    signal: float = 0.30
    impact: float = 0.30

    def __post_init__(self):
        total = self.reputation + self.signal + self.impact
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Сумма весов должна быть 1.0, сейчас: {total}")


@dataclass
class TierThresholds:
    elite: int = 80
    premium: int = 60
    standard: int = 40


@dataclass
class LeaderboardCategory:
    """Категории лидерборда HackerOne"""
    REPUTATION = "reputation"
    HIGH_CRITICAL = "high_critical"
    OWASP = "owasp"
    COUNTRY = "country"
    ASSET_TYPE = "asset_type"
    UP_AND_COMERS = "up_and_comers"
    UPVOTES = "upvotes"

    URLS = {
        "reputation": "/leaderboard",
        "high_critical": "/leaderboard/high_critical",
        "owasp": "/leaderboard/owasp",
        "country": "/leaderboard/country",
        "asset_type": "/leaderboard/asset_type",
        "up_and_comers": "/leaderboard/up_and_comers",
        "upvotes": "/leaderboard/upvotes"
    }


@dataclass
class ScraperConfig:
    base_url: str = "https://hackerone.com"
    leaderboard_url: str = "https://hackerone.com/leaderboard"
    hacktivity_url: str = "https://hackerone.com/hacktivity"
    scroll_iterations: int = 5
    wait_timeout: int = 30
    default_category: str = "reputation"

    def __post_init__(self):
        self.base_url = self.base_url.strip()
        self.leaderboard_url = self.leaderboard_url.strip()
        self.hacktivity_url = self.hacktivity_url.strip()


@dataclass
class ExportConfig:
    formats: List[str] = field(default_factory=lambda: ["json", "csv"])
    output_dir: str = "processed"
    include_timestamp: bool = True
    export_excel: bool = False


@dataclass
class AnalysisConfig:
    min_hackers_for_analysis: int = 5
    include_recommendations: bool = True
    calculate_portfolio_stats: bool = True


@dataclass
class AppConfig:
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")

    processed_data_dir: str = "processed"
    debug_data_dir: str = "debug"

    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    metrics_weights: MetricsWeights = field(default_factory=MetricsWeights)
    tier_thresholds: TierThresholds = field(default_factory=TierThresholds)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)

    def __post_init__(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / self.processed_data_dir).mkdir(exist_ok=True)
        (self.data_dir / self.debug_data_dir).mkdir(exist_ok=True)

    @classmethod
    def from_yaml(cls, config_path: Optional[Path] = None) -> 'AppConfig':
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        if not config_path.exists():
            return cls()
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            if not config_data:
                return cls()
            hackerone_config = config_data.get('hackerone', {})
            analysis_config = config_data.get('analysis', {})
            export_config = config_data.get('export', {})
            return cls(
                rate_limit=RateLimitConfig(**hackerone_config.get('api', {}).get('rate_limit', {})),
                scraper=ScraperConfig(**hackerone_config.get('scraper', {})),
                metrics_weights=MetricsWeights(**analysis_config.get('metrics_weights', {})),
                tier_thresholds=TierThresholds(**analysis_config.get('tier_thresholds', {})),
                export=ExportConfig(**export_config)
            )
        except Exception as e:
            print(f"⚠ Ошибка загрузки config.yaml: {e}")
            return cls()

    def to_dict(self) -> Dict:
        return {
            'hackerone': {
                'api': {
                    'rate_limit': {
                        'requests_per_minute': self.rate_limit.requests_per_minute,
                        'delay_between_requests': self.rate_limit.delay_between_requests,
                        'max_retries': self.rate_limit.max_retries,
                        'timeout': self.rate_limit.timeout
                    }
                },
                'scraper': {
                    'base_url': self.scraper.base_url,
                    'leaderboard_url': self.scraper.leaderboard_url,
                    'hacktivity_url': self.scraper.hacktivity_url,
                    'scroll_iterations': self.scraper.scroll_iterations,
                    'wait_timeout': self.scraper.wait_timeout,
                    'default_category': self.scraper.default_category
                }
            },
            'analysis': {
                'metrics_weights': {
                    'reputation': self.metrics_weights.reputation,
                    'signal': self.metrics_weights.signal,
                    'impact': self.metrics_weights.impact
                },
                'tier_thresholds': {
                    'elite': self.tier_thresholds.elite,
                    'premium': self.tier_thresholds.premium,
                    'standard': self.tier_thresholds.standard
                }
            },
            'export': {
                'formats': self.export.formats,
                'output_dir': self.export.output_dir,
                'include_timestamp': self.export.include_timestamp,
                'export_excel': self.export.export_excel
            }
        }

    def save_to_yaml(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)