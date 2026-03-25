import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from src.models.entities import HackerProfile, BugReport, HackerTier, HackerValueAnalysis

logger = logging.getLogger(__name__)


class HackerAnalyzer:
    """
    Анализ отдельных хакеров

    ✅ Что делает:
    - Рассчитывает value_score, activity_score, quality_score
    - Определяет tier (elite/premium/standard/novice)
    - Определяет priority для рекрутинга
    - Генерирует рекомендации
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            'reputation': 0.40,
            'signal': 0.30,
            'impact': 0.30
        }

        self.tier_thresholds = {
            'elite': 80,
            'premium': 60,
            'standard': 40,
            'novice': 0
        }

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
        norm_signal = min(profile.signal / 100, 1.0)
        norm_impact = min(profile.impact / 50000, 1.0)

        score = (
                self.weights['reputation'] * norm_rep +
                self.weights['signal'] * norm_signal +
                self.weights['impact'] * norm_impact
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
                (20 if profile.is_verified else 0)
        )
        return round(min(100, score), 2)

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
        return round(min(100, score), 2)

    def determine_tier(self, value_score: float) -> HackerTier:
        """
        Определение tier хакера по value_score

        | Score  | Tier     | Описание                    |
        |--------|----------|-----------------------------|
        | ≥ 80   | elite    | Топ-уровень, приоритет #1  |
        | ≥ 60   | premium  | Высокий уровень            |
        | ≥ 40   | standard | Средний уровень            |
        | < 40   | novice   | Начинающий                 |
        """
        if value_score >= self.tier_thresholds['elite']:
            return HackerTier.ELITE
        elif value_score >= self.tier_thresholds['premium']:
            return HackerTier.PREMIUM
        elif value_score >= self.tier_thresholds['standard']:
            return HackerTier.STANDARD
        return HackerTier.NOVICE

    def calculate_priority(self, tier: HackerTier, activity_score: float) -> str:
        """
        Расчёт приоритета для рекрутинга

        Returns:
            'high', 'medium', или 'low'
        """
        if tier in [HackerTier.ELITE, HackerTier.PREMIUM] and activity_score > 50:
            return 'high'
        elif tier in [HackerTier.PREMIUM, HackerTier.STANDARD]:
            return 'medium'
        return 'low'

    def generate_strengths(self, profile: HackerProfile) -> List[str]:
        """Генерация списка сильных сторон хакера"""
        strengths = []

        if profile.value_score >= 80:
            strengths.append("Высокая общая ценность")
        if profile.acceptance_rate >= 0.7:
            strengths.append("Высокий процент принятия отчётов")
        if profile.total_reports >= 50:
            strengths.append("Большой опыт (50+ отчётов)")
        if profile.is_verified:
            strengths.append("Верифицированный хакер")
        if profile.signal >= 80:
            strengths.append("Высокий сигнал качества")
        if profile.impact >= 30000:
            strengths.append("Значительный impact")
        if len(profile.skills) >= 3:
            strengths.append(f"Разнообразные навыки: {', '.join(profile.skills[:3])}")

        return strengths

    def generate_weaknesses(self, profile: HackerProfile) -> List[str]:
        """Генерация списка слабых сторон хакера"""
        weaknesses = []

        if profile.acceptance_rate < 0.3:
            weaknesses.append("Низкий процент принятия отчётов")
        if profile.total_reports < 10:
            weaknesses.append("Мало отчётов (< 10)")
        if profile.signal < 50:
            weaknesses.append("Низкий сигнал качества")
        if profile.impact < 5000:
            weaknesses.append("Низкий impact")
        if not profile.is_verified:
            weaknesses.append("Не верифицирован")
        if len(profile.skills) == 0:
            weaknesses.append("Навыки не указаны")

        return weaknesses

    def generate_recommendations(self, profile: HackerProfile) -> List[str]:
        """Генерация рекомендаций по работе с хакером"""
        recommendations = []

        if profile.tier == HackerTier.ELITE:
            recommendations.append("Приоритетное привлечение в программу")
            recommendations.append("Предложить персональные условия сотрудничества")
        elif profile.tier == HackerTier.PREMIUM:
            recommendations.append("Стандартное привлечение в программу")
            recommendations.append("Мониторить активность")
        elif profile.tier == HackerTier.STANDARD:
            recommendations.append("Добавить в базу потенциальных хакеров")
            recommendations.append("Отслеживать прогресс")
        else:
            recommendations.append("Мониторинг активности")
            recommendations.append("Предложить обучение/менторство")

        if profile.acceptance_rate < 0.5:
            recommendations.append("Улучшить качество отчётов (низкий acceptance rate)")

        if profile.total_reports < 20:
            recommendations.append("Поощрить активность (мало отчётов)")

        return recommendations

    def analyze(self, profile: HackerProfile) -> HackerValueAnalysis:
        """
        Полный анализ профиля хакера

        Returns:
            HackerValueAnalysis с метриками и рекомендациями
        """
        # ✅ ИСПРАВЛЕНО: Обновляем метрики в профиле
        profile.value_score = self.calculate_value_score(profile)
        profile.activity_score = self.calculate_activity_score(profile)
        profile.quality_score = self.calculate_quality_score(profile)
        profile.tier = self.determine_tier(profile.value_score)

        # Генерация анализа
        strengths = self.generate_strengths(profile)
        weaknesses = self.generate_weaknesses(profile)
        recommendations = self.generate_recommendations(profile)
        priority = self.calculate_priority(profile.tier, profile.activity_score)

        analysis = HackerValueAnalysis(
            username=profile.username,
            value_score=profile.value_score,
            activity_score=profile.activity_score,
            quality_score=profile.quality_score,
            tier=profile.tier,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            recruitment_priority=priority,
            analyzed_at=datetime.now()
        )

        logger.debug(f"Анализ хакера {profile.username}: tier={profile.tier.value}, "
                     f"value={profile.value_score}, priority={priority}")

        return analysis

    def analyze_batch(self, profiles: List[HackerProfile]) -> List[HackerValueAnalysis]:
        """
        Массовый анализ списка хакеров

        Args:
            profiles: Список профилей для анализа

        Returns:
            Список результатов анализа
        """
        logger.info(f"📈 Анализ {len(profiles)} хакеров...")

        analyses = []
        for profile in profiles:
            try:
                analysis = self.analyze(profile)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"❌ Ошибка анализа хакера {profile.username}: {e}")
                continue

        logger.info(f"✓ Проанализировано {len(analyses)} из {len(profiles)} хакеров")

        return analyses


class PortfolioAnalyzer:
    """
    Анализ портфеля хакеров

    ✅ Что делает:
    - Анализирует распределение навыков
    - Анализирует географию
    - Выявляет тренды
    - Считает общую статистику
    """

    @staticmethod
    def analyze_specialization(profiles: List[HackerProfile]) -> Dict[str, int]:
        """
        Анализ распределения навыков среди хакеров

        Returns:
            Dict с навыками и количеством хакеров
        """
        skills_count = {}

        for profile in profiles:
            for skill in profile.skills:
                skill_normalized = skill.strip().lower()
                skills_count[skill_normalized] = skills_count.get(skill_normalized, 0) + 1

        # Сортировка по популярности
        sorted_skills = dict(
            sorted(skills_count.items(), key=lambda x: x[1], reverse=True)
        )

        logger.debug(f"📊 Распределение навыков: {sorted_skills}")

        return sorted_skills

    @staticmethod
    def analyze_geography(profiles: List[HackerProfile]) -> Dict[str, Dict[str, Any]]:
        """
        Анализ географического распределения

        Returns:
            Dict со странами и статистикой
        """
        country_stats = {}

        for profile in profiles:
            country = profile.country or "Unknown"

            if country not in country_stats:
                country_stats[country] = {
                    'count': 0,
                    'total_value_score': 0,
                    'total_reputation': 0,
                    'hackers': []
                }

            country_stats[country]['count'] += 1
            country_stats[country]['total_value_score'] += profile.value_score
            country_stats[country]['total_reputation'] += profile.reputation
            country_stats[country]['hackers'].append(profile.username)

        # Расчёт средних значений
        for country in country_stats:
            count = country_stats[country]['count']
            country_stats[country]['avg_value_score'] = round(
                country_stats[country]['total_value_score'] / count, 2
            )
            country_stats[country]['avg_reputation'] = round(
                country_stats[country]['total_reputation'] / count, 2
            )

        # Сортировка по количеству хакеров
        sorted_countries = dict(
            sorted(country_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        )

        logger.debug(f"🌍 География: {len(sorted_countries)} стран")

        return sorted_countries

    @staticmethod
    def analyze_tier_distribution(profiles: List[HackerProfile]) -> Dict[str, int]:
        """
        Анализ распределения по tier

        Returns:
            Dict с tier и количеством хакеров
        """
        tier_count = {}

        for profile in profiles:
            tier = profile.tier.value
            tier_count[tier] = tier_count.get(tier, 0) + 1

        logger.debug(f"📊 Распределение по tier: {tier_count}")

        return tier_count

    @staticmethod
    def calculate_portfolio_stats(profiles: List[HackerProfile]) -> Dict[str, Any]:
        """
        Расчёт общей статистики портфеля

        Returns:
            Dict со статистикой
        """
        if not profiles:
            return {}

        total = len(profiles)
        avg_value = sum(p.value_score for p in profiles) / total
        avg_activity = sum(p.activity_score for p in profiles) / total
        avg_quality = sum(p.quality_score for p in profiles) / total
        avg_reputation = sum(p.reputation for p in profiles) / total

        # Процент верифицированных
        verified_count = sum(1 for p in profiles if p.is_verified)
        verified_percent = round((verified_count / total) * 100, 2)

        stats = {
            'total_hackers': total,
            'avg_value_score': round(avg_value, 2),
            'avg_activity_score': round(avg_activity, 2),
            'avg_quality_score': round(avg_quality, 2),
            'avg_reputation': round(avg_reputation, 2),
            'verified_percent': verified_percent,
            'elite_count': sum(1 for p in profiles if p.tier == HackerTier.ELITE),
            'premium_count': sum(1 for p in profiles if p.tier == HackerTier.PREMIUM),
            'standard_count': sum(1 for p in profiles if p.tier == HackerTier.STANDARD),
            'novice_count': sum(1 for p in profiles if p.tier == HackerTier.NOVICE)
        }

        logger.info(f"📊 Статистика портфеля: {stats}")

        return stats


class ReportAnalyzer:
    """
    Анализ отчётов о уязвимостях

    ✅ Что делает:
    - Анализирует распределение по severity
    - Анализирует распределение по state
    - Считает общую сумму баунти
    - Анализирует по программам
    """

    @staticmethod
    def analyze_by_severity(reports: List[BugReport]) -> Dict[str, int]:
        """
        Анализ распределения отчётов по severity

        Returns:
            Dict с severity и количеством отчётов
        """
        severity_count = {}

        for report in reports:
            severity = report.severity or "unknown"
            severity_count[severity] = severity_count.get(severity, 0) + 1

        # Сортировка по приоритету severity
        priority_order = ['critical', 'high', 'medium', 'low', 'unknown']
        sorted_severity = {}

        for severity in priority_order:
            if severity in severity_count:
                sorted_severity[severity] = severity_count[severity]

        # Добавляем остальные
        for severity in severity_count:
            if severity not in sorted_severity:
                sorted_severity[severity] = severity_count[severity]

        logger.debug(f"📊 Распределение по severity: {sorted_severity}")

        return sorted_severity

    @staticmethod
    def analyze_by_state(reports: List[BugReport]) -> Dict[str, int]:
        """
        Анализ распределения отчётов по state

        Returns:
            Dict с state и количеством отчётов
        """
        state_count = {}

        for report in reports:
            state = report.state.value if hasattr(report.state, 'value') else str(report.state)
            state_count[state] = state_count.get(state, 0) + 1

        logger.debug(f"📊 Распределение по state: {state_count}")

        return state_count

    @staticmethod
    def calculate_total_bounties(reports: List[BugReport]) -> float:
        """
        Расчёт общей суммы баунти

        Returns:
            Общая сумма в долларах
        """
        total = sum(report.bounty_amount for report in reports)
        logger.debug(f"💰 Общая сумма баунти: ${total:,.2f}")
        return round(total, 2)

    @staticmethod
    def calculate_avg_bounty(reports: List[BugReport]) -> float:
        """
        Расчёт среднего баунти

        Returns:
            Среднее значение в долларах
        """
        if not reports:
            return 0.0

        total = sum(report.bounty_amount for report in reports)
        avg = total / len(reports)

        logger.debug(f"💰 Средний баунти: ${avg:,.2f}")

        return round(avg, 2)

    @staticmethod
    def analyze_by_program(reports: List[BugReport]) -> Dict[str, int]:
        """
        Анализ распределения отчётов по программам

        Returns:
            Dict с программами и количеством отчётов
        """
        program_count = {}

        for report in reports:
            program = report.program_name or "Unknown"
            program_count[program] = program_count.get(program, 0) + 1

        # Сортировка по количеству
        sorted_programs = dict(
            sorted(program_count.items(), key=lambda x: x[1], reverse=True)
        )

        logger.debug(f"📊 Распределение по программам: {sorted_programs}")

        return sorted_programs

    @staticmethod
    def analyze_by_hacker(reports: List[BugReport]) -> Dict[str, Dict[str, Any]]:
        """
        Анализ активности хакеров по отчётам

        Returns:
            Dict с хакерами и их статистикой
        """
        hacker_stats = {}

        for report in reports:
            hacker = report.hacker_username or "unknown"

            if hacker not in hacker_stats:
                hacker_stats[hacker] = {
                    'report_count': 0,
                    'total_bounty': 0.0,
                    'reports': []
                }

            hacker_stats[hacker]['report_count'] += 1
            hacker_stats[hacker]['total_bounty'] += report.bounty_amount
            hacker_stats[hacker]['reports'].append(report.report_id)

        # Расчёт среднего баунти
        for hacker in hacker_stats:
            count = hacker_stats[hacker]['report_count']
            hacker_stats[hacker]['avg_bounty'] = round(
                hacker_stats[hacker]['total_bounty'] / count, 2
            ) if count > 0 else 0.0

        # Сортировка по количеству отчётов
        sorted_hackers = dict(
            sorted(hacker_stats.items(), key=lambda x: x[1]['report_count'], reverse=True)
        )

        logger.debug(f"📊 Активность хакеров: {len(sorted_hackers)} хакеров")

        return sorted_hackers


class RecruitmentAnalyzer:
    """
    Анализ для рекрутинга хакеров

    ✅ Что делает:
    - Определяет приоритетные цели для рекрутинга
    - Генерирует списки для outreach
    - Считывает ROI потенциальных хакеров
    """

    def __init__(self):
        self.priority_weights = {
            'elite': 100,
            'premium': 75,
            'standard': 50,
            'novice': 25
        }

    def calculate_recruitment_score(self, analysis: HackerValueAnalysis) -> float:
        """
        Расчёт scores для рекрутинга

        Returns:
            Score 0-100 для приоритизации
        """
        tier_score = self.priority_weights.get(analysis.tier.value, 0)
        activity_bonus = analysis.activity_score * 0.3
        quality_bonus = analysis.quality_score * 0.2

        total = tier_score + activity_bonus + quality_bonus

        return round(min(100, total), 2)

    def generate_priority_list(
            self,
            analyses: List[HackerValueAnalysis],
            min_score: float = 50,
            limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Генерация приоритетного списка для рекрутинга

        Args:
            analyses: Список анализов хакеров
            min_score: Минимальный recruitment score
            limit: Максимальное количество в списке

        Returns:
            Список хакеров с приоритетами
        """
        priority_list = []

        for analysis in analyses:
            recruitment_score = self.calculate_recruitment_score(analysis)

            if recruitment_score >= min_score:
                priority_list.append({
                    'username': analysis.username,
                    'tier': analysis.tier.value,
                    'value_score': analysis.value_score,
                    'recruitment_score': recruitment_score,
                    'priority': analysis.recruitment_priority,
                    'strengths': analysis.strengths[:3],
                    'recommendations': analysis.recommendations[:2]
                })

        # Сортировка по recruitment score
        priority_list.sort(key=lambda x: x['recruitment_score'], reverse=True)

        return priority_list[:limit]

    def generate_outreach_template(self, analysis: HackerValueAnalysis) -> str:
        """
        Генерация шаблона письма для outreach

        Args:
            analysis: Анализ хакера

        Returns:
            Текст шаблона письма
        """
        tier_emoji = {
            'elite': '🏆',
            'premium': '⭐',
            'standard': '🎯',
            'novice': '🌱'
        }

        template = f"""
Subject: Invitation to Join Our Bug Bounty Program

Dear {analysis.username},

{tier_emoji.get(analysis.tier.value, '👋')} We've been impressed by your work on HackerOne!

Your Profile:
• Tier: {analysis.tier.value.upper()}
• Value Score: {analysis.value_score}/100
• Strengths: {', '.join(analysis.strengths[:2])}

We'd love to invite you to join our bug bounty program with:
{chr(10).join('• ' + rec for rec in analysis.recommendations[:2])}

Would you be interested in learning more?

Best regards,
Security Team
"""

        return template.strip()