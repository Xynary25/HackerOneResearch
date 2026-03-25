import logging
from typing import List, Dict
from src.models.entities import HackerProfile, HackerTier
from src.config.settings import AppConfig

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Нормализация данных

    ✅ Что делает:
    - Приводит значения к стандартному диапазону
    - Заполняет пропуски
    - Валидирует типы данных
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

            # Total bounties: не отрицательное
            profile.total_bounties = max(0.0, profile.total_bounties)

            # Total reports: не отрицательное
            profile.total_reports = max(0, profile.total_reports)

            # Accepted reports: не отрицательное
            profile.accepted_reports = max(0, profile.accepted_reports)

        logger.info(f"✓ Нормализовано {len(profiles)} профилей")
        return profiles


class DataEnricher:
    """
    Обогащение данных вычисляемыми метриками

    ✅ Формулы:
    - value_score = 0.40*rep + 0.30*signal + 0.30*impact
    - activity_score = reports*0.4 + acceptance*40 + verified*20
    - quality_score = acceptance*50 + bounty*30 + impact*20
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self.weights = config.metrics_weights
        self.thresholds = config.tier_thresholds

    def calculate_value_score(self, profile: HackerProfile) -> float:
        """
        Расчёт общего value_score (0-100)

        Формула:
        value_score = (
            0.40 * normalize(reputation, 0, 10000) +
            0.30 * normalize(signal, 0, 100) +
            0.30 * normalize(impact, 0, 50000)
        )
        """
        norm_rep = min(profile.reputation / 10000, 1.0)
        norm_signal = profile.signal / 100
        norm_impact = min(profile.impact / 50000, 1.0)

        score = (
                self.weights.reputation * norm_rep +
                self.weights.signal * norm_signal +
                self.weights.impact * norm_impact
        )

        return round(score * 100, 2)

    def calculate_activity_score(self, profile: HackerProfile) -> float:
        """
        Расчёт activity_score (0-100)
        На основе активности хакера
        """
        score = (
                min(profile.total_reports / 100, 1.0) * 40 +
                profile.acceptance_rate * 40 +
                (1 if profile.is_verified else 0) * 20
        )
        return min(100, round(score, 2))

    def calculate_quality_score(self, profile: HackerProfile) -> float:
        """
        Расчёт quality_score (0-100)
        На основе качества отчётов
        """
        avg_bounty = profile.total_bounties / max(profile.total_reports, 1)

        score = (
                profile.acceptance_rate * 50 +
                min(avg_bounty / 1000, 1.0) * 30 +
                min(profile.impact / 50000, 1.0) * 20
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
            profile.tier = self.determine_tier(profile.value_score)

        logger.info(f"✓ Обогащено {len(profiles)} профилей метриками")
        return profiles


class DataFilter:
    """
    Фильтрация данных

    ✅ Фильтры:
    - По tier (elite, premium, standard, novice)
    - По минимальному score
    - По стране
    - По активности (минимум отчётов)
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

    ✅ Методы:
    - Группировка по tier
    - Группировка по стране
    - Расчёт статистик (среднее, всего)
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
    def aggregate_by_skills(profiles: List[HackerProfile]) -> Dict[str, int]:
        """Группировка по навыкам"""
        result = {}
        for p in profiles:
            for skill in p.skills:
                result[skill] = result.get(skill, 0) + 1
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

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
            "total_hackers": len(profiles),
            "max_value_score": round(max(p.value_score for p in profiles), 2),
            "min_value_score": round(min(p.value_score for p in profiles), 2),
        }