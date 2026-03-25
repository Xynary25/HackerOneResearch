from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class HackerTier(Enum):
    """
    Уровни хакеров на основе value_score

    | Score  | Tier     | Описание                    |
    |--------|----------|-----------------------------|
    | ≥ 80   | elite    | Топ-уровень, приоритет #1  |
    | ≥ 60   | premium  | Высокий уровень            |
    | ≥ 40   | standard | Средний уровень            |
    | < 40   | novice   | Начинающий                 |
    """
    NOVICE = "novice"
    STANDARD = "standard"
    PREMIUM = "premium"
    ELITE = "elite"


class ReportState(Enum):
    """Состояния отчётов об уязвимостях"""
    NEW = "new"
    TRIAGED = "triaged"
    RESOLVED = "resolved"
    CLOSED = "closed"


class LeaderboardCategory(Enum):
    """Категории лидерборда HackerOne"""
    REPUTATION = "reputation"
    HIGH_CRITICAL = "high_critical"
    OWASP = "owasp"
    COUNTRY = "country"
    ASSET_TYPE = "asset_type"
    UP_AND_COMERS = "up_and_comers"
    UPVOTES = "upvotes"


@dataclass
class HackerProfile:
    """
    Профиль хакера с метриками

    ✅ Поля из лидерборда:
    - username, reputation, signal, impact

    ✅ Вычисляемые метрики:
    - value_score, activity_score, quality_score
    - tier, acceptance_rate
    """
    username: str
    reputation: int = 0
    signal: float = 0.0
    impact: int = 0
    total_bounties: float = 0.0
    total_reports: int = 0
    accepted_reports: int = 0
    acceptance_rate: float = 0.0
    rank: Optional[int] = None
    country: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    is_verified: bool = False
    tier: HackerTier = HackerTier.NOVICE
    value_score: float = 0.0
    activity_score: float = 0.0
    quality_score: float = 0.0
    last_activity_date: Optional[datetime] = None
    profile_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для экспорта (JSON/CSV/Excel)"""
        return {
            "username": self.username,
            "reputation": self.reputation,
            "signal": round(self.signal, 2),
            "impact": self.impact,
            "total_bounties": round(self.total_bounties, 2),
            "total_reports": self.total_reports,
            "accepted_reports": self.accepted_reports,
            "acceptance_rate": round(self.acceptance_rate, 2),
            "country": self.country or "Unknown",
            "is_verified": self.is_verified,
            "tier": self.tier.value,
            "value_score": round(self.value_score, 2),
            "activity_score": round(self.activity_score, 2),
            "quality_score": round(self.quality_score, 2),
            "skills": ", ".join(self.skills) if self.skills else "None",
            "profile_url": self.profile_url or f"https://hackerone.com/{self.username}",
            "rank": self.rank or 0,
            "last_activity_date": str(self.last_activity_date) if self.last_activity_date else None,
        }

    def __str__(self) -> str:
        return f"HackerProfile({self.username}, tier={self.tier.value}, score={self.value_score})"


@dataclass
class BugReport:
    """
    Отчёт об уязвимости из Hacktivity

    ✅ Поля:
    - report_id, title, state
    - hacker_username, program_name
    - bounty_amount, severity
    """
    report_id: int
    title: str
    state: ReportState
    hacker_username: str
    program_name: str
    bounty_amount: float = 0.0
    severity: Optional[str] = None
    disclosed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для экспорта (JSON/CSV/Excel)"""
        return {
            "report_id": self.report_id,
            "title": self.title[:200] if self.title else "",
            "state": self.state.value,
            "hacker_username": self.hacker_username or "Unknown",
            "program_name": self.program_name or "Unknown",
            "bounty_amount": round(self.bounty_amount, 2),
            "severity": self.severity or "unknown",
            "disclosed_at": str(self.disclosed_at) if self.disclosed_at else datetime.now().isoformat(),
        }

    def __str__(self) -> str:
        return f"BugReport(#{self.report_id}, {self.title[:50]})"


@dataclass
class HackerValueAnalysis:
    """
    Результат анализа хакера

    ✅ Используется для:
    - Рекомендаций по рекрутингу
    - Приоритизации контактов
    - Отчётности для Standoff
    """
    username: str
    value_score: float
    activity_score: float
    quality_score: float
    tier: HackerTier
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    recruitment_priority: str = "medium"
    analyzed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для экспорта (JSON/CSV/Excel)"""
        return {
            "username": self.username,
            "value_score": round(self.value_score, 2),
            "activity_score": round(self.activity_score, 2),
            "quality_score": round(self.quality_score, 2),
            "tier": self.tier.value,
            "strengths": ", ".join(self.strengths) if self.strengths else "None",
            "weaknesses": ", ".join(self.weaknesses) if self.weaknesses else "None",
            "recommendations": ", ".join(self.recommendations) if self.recommendations else "None",
            "recruitment_priority": self.recruitment_priority,
            "analyzed_at": str(self.analyzed_at) if self.analyzed_at else datetime.now().isoformat(),
        }

    def __str__(self) -> str:
        return f"HackerValueAnalysis({self.username}, priority={self.recruitment_priority})"