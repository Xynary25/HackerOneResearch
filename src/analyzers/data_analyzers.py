import logging
from typing import List, Dict
from src.models.entities import HackerProfile, HackerValueAnalysis, HackerTier, BugReport

logger = logging.getLogger(__name__)


class HackerAnalyzer:
    def analyze(self, profile: HackerProfile) -> HackerValueAnalysis:
        strengths = []
        weaknesses = []
        recommendations = []

        if profile.value_score >= 80:
            strengths.append("Высокая общая ценность")
        if profile.acceptance_rate >= 0.7:
            strengths.append("Высокий процент принятия")
        if profile.total_reports >= 50:
            strengths.append("Большой опыт")
        if profile.is_verified:
            strengths.append("Верифицированный хакер")

        if profile.acceptance_rate < 0.3:
            weaknesses.append("Низкий процент принятия")
        if profile.total_reports < 10:
            weaknesses.append("Мало отчётов")
        if profile.signal < 50:
            weaknesses.append("Низкий сигнал")

        if profile.tier == HackerTier.ELITE:
            recommendations.append("Приоритетное привлечение")
            priority = "high"
        elif profile.tier == HackerTier.PREMIUM:
            recommendations.append("Стандартное привлечение")
            priority = "medium"
        else:
            recommendations.append("Мониторинг активности")
            priority = "low"

        return HackerValueAnalysis(
            username=profile.username,
            value_score=profile.value_score,
            activity_score=profile.activity_score,
            quality_score=profile.quality_score,
            tier=profile.tier,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            recruitment_priority=priority
        )

    def analyze_batch(self, profiles: List[HackerProfile]) -> List[HackerValueAnalysis]:
        return [self.analyze(p) for p in profiles]


class PortfolioAnalyzer:
    @staticmethod
    def analyze_specialization(profiles: List[HackerProfile]) -> Dict[str, int]:
        skills_count = {}
        for p in profiles:
            for skill in p.skills:
                skills_count[skill] = skills_count.get(skill, 0) + 1
        return dict(sorted(skills_count.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def analyze_geography(profiles: List[HackerProfile]) -> Dict[str, float]:
        country_scores = {}
        country_counts = {}
        for p in profiles:
            country = p.country or "Unknown"
            country_scores[country] = country_scores.get(country, 0) + p.value_score
            country_counts[country] = country_counts.get(country, 0) + 1
        return {c: round(country_scores[c] / country_counts[c], 2) for c in country_scores}


class ReportAnalyzer:
    @staticmethod
    def analyze_by_severity(reports: List[BugReport]) -> Dict[str, int]:
        result = {}
        for r in reports:
            sev = r.severity or "unknown"
            result[sev] = result.get(sev, 0) + 1
        return result

    @staticmethod
    def analyze_by_state(reports: List[BugReport]) -> Dict[str, int]:
        result = {}
        for r in reports:
            result[r.state.value] = result.get(r.state.value, 0) + 1
        return result

    @staticmethod
    def calculate_total_bounties(reports: List[BugReport]) -> float:
        return sum(r.bounty_amount for r in reports)