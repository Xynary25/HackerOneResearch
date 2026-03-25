from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class HackerTier(Enum):
    NOVICE = "novice"
    STANDARD = "standard"
    PREMIUM = "premium"
    ELITE = "elite"


class ReportState(Enum):
    NEW = "new"
    TRIAGED = "triaged"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class HackerProfile:
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
        return {
            "username": self.username,
            "reputation": self.reputation,
            "signal": round(self.signal, 2),
            "impact": self.impact,
            "total_bounties": round(self.total_bounties, 2),
            "total_reports": self.total_reports,
            "accepted_reports": self.accepted_reports,
            "acceptance_rate": round(self.acceptance_rate, 2),
            "country": self.country,
            "is_verified": self.is_verified,
            "tier": self.tier.value,
            "value_score": round(self.value_score, 2),
            "activity_score": round(self.activity_score, 2),
            "quality_score": round(self.quality_score, 2),
            "skills": self.skills,
            "profile_url": self.profile_url,
        }


@dataclass
class BugReport:
    report_id: int
    title: str
    state: ReportState
    hacker_username: str
    program_name: str
    bounty_amount: float = 0.0
    severity: Optional[str] = None
    disclosed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "state": self.state.value,
            "hacker_username": self.hacker_username,
            "program_name": self.program_name,
            "bounty_amount": round(self.bounty_amount, 2),
            "severity": self.severity,
            "disclosed_at": str(self.disclosed_at) if self.disclosed_at else None,
        }


@dataclass
class HackerValueAnalysis:
    username: str
    value_score: float
    activity_score: float
    quality_score: float
    tier: HackerTier
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    recruitment_priority: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "value_score": round(self.value_score, 2),
            "tier": self.tier.value,
            "strengths": self.strengths,
            "recommendations": self.recommendations,
            "recruitment_priority": self.recruitment_priority,
        }