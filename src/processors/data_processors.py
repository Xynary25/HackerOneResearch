import logging
from typing import List, Dict
from src.models.entities import HackerProfile, HackerTier
from src.config.settings import AppConfig

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Нормализация данных
    ✅ Приводит значения к стандартному диапазону
    ✅ Заполняет пропуски
    ✅ Удаляет дубликаты
    """

    def __init__(self, config: AppConfig):
        self.config = config

    def normalize(self, profiles: List[HackerProfile]) -> List[HackerProfile]:
        """Нормализация профилей хакеров"""
        for profile in profiles:
            # Signal: 0-100
            profile.signal = min(100.0, max(0.0, profile.signal))

            # Acceptance rate: 0-1
            profile.acceptance_rate = min(1.0, max(0.0, profile.acceptance_rate))

            # Reputation: не отрицательное
            profile.reputation = max(0, profile.reputation)

            # Impact: не отрицательное
            profile.impact = max(0, profile.impact)

        logger.info(f"✓ Нормализовано {len(profiles)} профилей")
        return profiles


class DataEnricher:
    """
    Обогащение данных вычисляемыми метриками
    ✅ Рассчитывает value_score, activity_score, quality_score
    ✅ Определяет tier хакера
    ✅ Использует улучшенную формулу рейтинга
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self.weights = config.metrics_weights
        self.advanced_weights = config.advanced_metrics_weights
        self.thresholds = config.tier_thresholds

    def calculate_value_score(self, profile: HackerProfile) -> float:
        """
        Улучшенный расчёт общего value_score (0-100)

        Новая формула учитывает больше факторов:
        - Репутация (нормализованная)
        - Signal (нормализованный)
        - Impact (нормализованный)
        - Acceptance rate
        - Активность (recency фактор)
        """
        norm_rep = min(profile.reputation / 10000, 1.0)
        norm_signal = profile.signal / 100
        norm_impact = min(profile.impact / 50000, 1.0)
        norm_acceptance = profile.acceptance_rate
        
        recency_factor = 1.0
        if profile.last_activity_date:
            days_since_activity = (datetime.now() - profile.last_activity_date).days
            recency_factor = max(0.5, 1.0 - (days_since_activity / 365))

        score = (
            self.weights.reputation * norm_rep +
            self.weights.signal * norm_signal +
            self.weights.impact * norm_impact +
            self.weights.acceptance_rate * norm_acceptance +
            self.weights.activity_recency * recency_factor
        )

        return round(score * 100, 2)

    def calculate_advanced_rating(self, profile: HackerProfile) -> float:
        """
        Расширенная формула рейтинга с дополнительными факторами

        Формула:
        rating = (
            0.15 * normalize(reputation) +
            0.15 * normalize(signal) +
            0.15 * normalize(impact) +
            0.20 * report_quality +
            0.15 * consistency_bonus +
            0.10 * recency_factor +
            0.10 * verification_bonus
        )
        """
        norm_rep = min(profile.reputation / 10000, 1.0)
        norm_signal = profile.signal / 100
        norm_impact = min(profile.impact / 50000, 1.0)
        
        report_quality = profile.acceptance_rate * min(profile.total_reports / 50, 1.0)
        
        consistency_bonus = min(profile.acceptance_rate * (1 + profile.total_reports / 100), 1.0)
        
        recency_factor = 1.0
        if profile.last_activity_date:
            days_since_activity = (datetime.now() - profile.last_activity_date).days
            recency_factor = max(0.3, 1.0 - (days_since_activity / 180))
        
        verification_bonus = 1.0 if profile.is_verified else 0.5

        score = (
            self.advanced_weights.base_reputation * norm_rep +
            self.advanced_weights.normalized_signal * norm_signal +
            self.advanced_weights.impact_score * norm_impact +
            self.advanced_weights.report_quality * report_quality +
            self.advanced_weights.consistency_bonus * consistency_bonus +
            self.advanced_weights.recency_factor * recency_factor +
            self.advanced_weights.verification_bonus * verification_bonus
        )

        return round(score * 100, 2)

    def calculate_activity_score(self, profile: HackerProfile) -> float:
        """
        Расчёт activity_score (0-100)
        На основе активности хакера
        """
        recency_bonus = 1.0
        if profile.last_activity_date:
            days_since_activity = (datetime.now() - profile.last_activity_date).days
            recency_bonus = max(0.5, 1.0 - (days_since_activity / 90))

        score = (
            min(profile.total_reports / 50, 1.0) * 40 +
            profile.acceptance_rate * 30 +
            (1 if profile.is_verified else 0) * 20 +
            recency_bonus * 10
        )
        return min(100, round(score, 2))

    def calculate_quality_score(self, profile: HackerProfile) -> float:
        """
        Расчёт quality_score (0-100)
        На основе качества отчётов
        """
        avg_bounty = profile.total_bounties / max(profile.total_reports, 1)
        
        bounty_quality = min(avg_bounty / 1500, 1.0)
        acceptance_quality = profile.acceptance_rate
        impact_quality = min(profile.impact / 50000, 1.0)

        score = (
            acceptance_quality * 40 +
            bounty_quality * 35 +
            impact_quality * 25
        )
        return min(100, round(score, 2))

    def determine_tier(self, value_score: float) -> HackerTier:
        """
        Определение tier хакера по value_score

        | Score  | Tier     |
        |--------|----------|
        | ≥ 80   | elite    |
        | ≥ 60   | premium  |
        | ≥ 40   | standard |
        | < 40   | novice   |
        """
        if value_score >= self.thresholds.elite:
            return HackerTier.ELITE
        elif value_score >= self.thresholds.premium:
            return HackerTier.PREMIUM
        elif value_score >= self.thresholds.standard:
            return HackerTier.STANDARD
        return HackerTier.NOVICE

    def enrich(self, profiles: List[HackerProfile]) -> List[HackerProfile]:
        """Обогащение всех профилей метриками"""
        for profile in profiles:
            profile.value_score = self.calculate_value_score(profile)
            profile.activity_score = self.calculate_activity_score(profile)
            profile.quality_score = self.calculate_quality_score(profile)
            
            if profile.value_score >= 70:
                profile.value_score = max(profile.value_score, self.calculate_advanced_rating(profile))
            
            profile.tier = self.determine_tier(profile.value_score)

        logger.info(f"✓ Обогащено {len(profiles)} профилей метриками")
        return profiles


class DataFilter:
    """
    Фильтрация данных
    ✅ По tier
    ✅ По минимальному score
    ✅ По стране
    ✅ По активности
    """

    def __init__(self, config: AppConfig):
        self.config = config

    def filter_by_tier(
            self,
            profiles: List[HackerProfile],
            min_tier: HackerTier
    ) -> List[HackerProfile]:
        """Фильтр по минимальному tier"""
        tier_order = [
            HackerTier.NOVICE,
            HackerTier.STANDARD,
            HackerTier.PREMIUM,
            HackerTier.ELITE
        ]
        min_idx = tier_order.index(min_tier)
        return [
            p for p in profiles
            if tier_order.index(p.tier) >= min_idx
        ]

    def filter_by_min_score(
            self,
            profiles: List[HackerProfile],
            min_score: float
    ) -> List[HackerProfile]:
        """Фильтр по минимальному value_score"""
        return [p for p in profiles if p.value_score >= min_score]

    def filter_by_country(
            self,
            profiles: List[HackerProfile],
            countries: List[str]
    ) -> List[HackerProfile]:
        """Фильтр по стране"""
        if not countries:
            return profiles
        return [p for p in profiles if p.country in countries]

    def filter_active(
            self,
            profiles: List[HackerProfile],
            min_reports: int = 10
    ) -> List[HackerProfile]:
        """Фильтр активных хакеров (минимум отчётов)"""
        return [p for p in profiles if p.total_reports >= min_reports]


class DataAggregator:
    """
    Агрегация данных
    ✅ Группировка по tier
    ✅ Группировка по стране
    ✅ Расчёт статистик
    """

    @staticmethod
    def aggregate_by_tier(profiles: List[HackerProfile]) -> Dict[str, int]:
        """Группировка по tier"""
        result = {}
        for p in profiles:
            tier = p.tier.value
            result[tier] = result.get(tier, 0) + 1
        return result

    @staticmethod
    def aggregate_by_country(profiles: List[HackerProfile]) -> Dict[str, int]:
        """Группировка по стране"""
        result = {}
        for p in profiles:
            country = p.country or "Unknown"
            result[country] = result.get(country, 0) + 1
        return result

    @staticmethod
    def calculate_stats(profiles: List[HackerProfile]) -> Dict[str, float]:
        """Расчёт статистик по выборке"""
        if not profiles:
            return {}

        return {
            "avg_value_score": round(
                sum(p.value_score for p in profiles) / len(profiles),
                2
            ),
            "avg_activity_score": round(
                sum(p.activity_score for p in profiles) / len(profiles),
                2
            ),
            "avg_quality_score": round(
                sum(p.quality_score for p in profiles) / len(profiles),
                2
            ),
            "total_hackers": len(profiles)
        }