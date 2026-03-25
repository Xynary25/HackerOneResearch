import logging
from typing import List, Dict
from datetime import datetime
from src.models.entities import HackerProfile, BugReport, ReportState
from src.clients.hackerone_scraper import HackerOneScraper

logger = logging.getLogger(__name__)


class BaseCollector:
    """Базовый класс для всех коллекторов"""

    def __init__(self, client: HackerOneScraper):
        self.client = client

    def collect(self, **kwargs) -> List:
        raise NotImplementedError


class LeaderboardCollector(BaseCollector):
    """
    Коллектор для сбора данных из лидерборда
    ✅ Преобразует сырые данные в объекты HackerProfile
    """

    def collect(self, limit: int = 100) -> List[HackerProfile]:
        logger.info(f"📊 Сбор лидерборда: {limit} хакеров")

        raw_data = self.client.fetch_leaderboard(limit)
        profiles = []

        for item in raw_data:
            profile = HackerProfile(
                username=item.get("username", ""),
                reputation=item.get("reputation", 0),
                signal=item.get("signal", 0.0),
                impact=item.get("impact", 0),
                total_bounties=item.get("total_bounties", 0.0),
                total_reports=item.get("total_reports", 0),
                accepted_reports=item.get("accepted_reports", 0),
                acceptance_rate=(
                        item.get("accepted_reports", 0) /
                        max(item.get("total_reports", 1), 1)
                ),
                rank=item.get("rank"),
                country=item.get("country"),
                skills=item.get("skills", []),
                is_verified=item.get("is_verified", False),
                last_activity_date=datetime.now(),
                profile_url=item.get("profile_url", "")
            )
            profiles.append(profile)

        logger.info(f"✓ Собрано {len(profiles)} профилей")
        return profiles


class HacktivityCollector(BaseCollector):
    """
    Коллектор для сбора данных из Hacktivity
    ✅ Преобразует сырые данные в объекты BugReport
    """

    def collect(self, limit: int = 50) -> List[BugReport]:
        logger.info(f"📰 Сбор hacktivity: {limit} отчётов")

        raw_data = self.client.fetch_hacktivity(limit)
        reports = []

        for item in raw_data:
            state_map = {
                "resolved": ReportState.RESOLVED,
                "triaged": ReportState.TRIAGED,
                "new": ReportState.NEW,
                "closed": ReportState.CLOSED
            }

            report = BugReport(
                report_id=item.get("report_id", 0),
                title=item.get("title", ""),
                state=state_map.get(
                    item.get("state", "triaged"),
                    ReportState.TRIAGED
                ),
                hacker_username=item.get("hacker_username", ""),
                program_name=item.get("program_name", ""),
                bounty_amount=item.get("bounty_amount", 0.0),
                severity=item.get("severity"),
                disclosed_at=datetime.now()
            )
            reports.append(report)

        logger.info(f"✓ Собрано {len(reports)} отчётов")
        return reports


class HackerProfileCollector(BaseCollector):
    """
    Коллектор для сбора детальных профилей
    ✅ Используется для углублённого сбора данных по конкретным username
    """

    def collect(self, usernames: List[str]) -> List[HackerProfile]:
        logger.info(f"👤 Сбор профилей: {len(usernames)} хакеров")

        profiles = []

        for username in usernames:
            raw_data = self.client.fetch_profile(username)

            if raw_data and raw_data.get('username'):
                profile = HackerProfile(
                    username=raw_data.get("username", username),
                    reputation=raw_data.get("reputation", 0),
                    signal=raw_data.get("signal", 0.0),
                    is_verified=raw_data.get("is_verified", False),
                    total_reports=raw_data.get("total_reports", 0),
                    accepted_reports=raw_data.get("accepted_reports", 0),
                    impact=raw_data.get("impact", 0),
                    total_bounties=raw_data.get("total_bounties", 0.0),
                    country=raw_data.get("country"),
                    skills=raw_data.get("skills", []),
                    last_activity_date=datetime.now(),
                    profile_url=f"https://hackerone.com/{username}"
                )
                profile.acceptance_rate = (
                        profile.accepted_reports /
                        max(profile.total_reports, 1)
                )
                profiles.append(profile)

        return profiles