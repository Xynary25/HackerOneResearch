#!/usr/bin/env python3
"""
Unit-тесты для HackerOne Research Tool

Запуск:
    pytest tests/ -v
    python -m unittest tests/test_all.py
"""
import unittest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Добавляем корень проекта в path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestModels(unittest.TestCase):
    """Тесты моделей данных"""

    def test_hacker_profile_creation(self):
        """Создание профиля хакера"""
        from src.models.entities import HackerProfile, HackerTier
        
        profile = HackerProfile(
            username="test_user",
            reputation=1000,
            signal=75.5,
            impact=500
        )
        
        self.assertEqual(profile.username, "test_user")
        self.assertEqual(profile.reputation, 1000)
        self.assertEqual(profile.tier, HackerTier.NOVICE)
        self.assertIsInstance(profile.skills, list)

    def test_hacker_profile_to_dict(self):
        """Конвертация профиля в словарь"""
        from src.models.entities import HackerProfile
        
        profile = HackerProfile(username="test", reputation=500)
        data = profile.to_dict()
        
        self.assertIn("username", data)
        self.assertEqual(data["username"], "test")
        self.assertEqual(data["reputation"], 500)

    def test_bug_report_creation(self):
        """Создание отчёта об уязвимости"""
        from src.models.entities import BugReport, ReportState
        
        report = BugReport(
            report_id=12345,
            title="XSS Vulnerability",
            state=ReportState.RESOLVED,
            hacker_username="hacker123",
            program_name="TestProgram",
            bounty_amount=500.0
        )
        
        self.assertEqual(report.report_id, 12345)
        self.assertEqual(report.state, ReportState.RESOLVED)
        self.assertEqual(report.bounty_amount, 500.0)

    def test_hacker_value_analysis(self):
        """Создание анализа ценности хакера"""
        from src.models.entities import HackerValueAnalysis, HackerTier
        
        analysis = HackerValueAnalysis(
            username="pro_hacker",
            value_score=85.5,
            activity_score=90.0,
            quality_score=80.0,
            tier=HackerTier.PREMIUM,
            strengths=["Web Security", "API Testing"],
            recruitment_priority="high"
        )
        
        self.assertEqual(analysis.username, "pro_hacker")
        self.assertEqual(analysis.tier, HackerTier.PREMIUM)
        self.assertIn("Web Security", analysis.strengths)


class TestDataExporters(unittest.TestCase):
    """Тесты экспортеров данных"""

    def setUp(self):
        """Подготовка тестовых данных"""
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_data = [
            {"username": "user1", "reputation": 100},
            {"username": "user2", "reputation": 200}
        ]

    def tearDown(self):
        """Очистка после теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_json_exporter(self):
        """Экспорт в JSON"""
        from src.exporters.data_exporters import JSONExporter
        
        exporter = JSONExporter(self.temp_dir)
        filepath = exporter.export(self.test_data, "test_hackers")
        
        self.assertTrue(Path(filepath).exists())
        self.assertTrue(filepath.endswith(".json"))

    def test_csv_exporter(self):
        """Экспорт в CSV"""
        from src.exporters.data_exporters import CSVExporter
        
        exporter = CSVExporter(self.temp_dir)
        filepath = exporter.export(self.test_data, "test_hackers")
        
        self.assertTrue(Path(filepath).exists())
        self.assertTrue(filepath.endswith(".csv"))

    def test_csv_exporter_empty_data(self):
        """Экспорт пустых данных в CSV"""
        from src.exporters.data_exporters import CSVExporter
        
        exporter = CSVExporter(self.temp_dir)
        filepath = exporter.export([], "empty")
        
        self.assertEqual(filepath, "")

    def test_json_exporter_context_manager(self):
        """JSONExporter как контекстный менеджер"""
        from src.exporters.data_exporters import JSONExporter
        
        with JSONExporter(self.temp_dir) as exporter:
            filepath = exporter.export(self.test_data, "context_test")
            self.assertTrue(Path(filepath).exists())

    def test_csv_exporter_context_manager(self):
        """CSVExporter как контекстный менеджер"""
        from src.exporters.data_exporters import CSVExporter
        
        with CSVExporter(self.temp_dir) as exporter:
            filepath = exporter.export(self.test_data, "context_test")
            self.assertTrue(Path(filepath).exists())


class TestHelpers(unittest.TestCase):
    """Тесты вспомогательных функций"""

    def test_sanitize_value_none(self):
        """Санитизация None значения"""
        from src.utils.helpers import sanitize_value
        
        result = sanitize_value(None)
        self.assertEqual(result, "")

    def test_sanitize_value_list(self):
        """Санитизация списка"""
        from src.utils.helpers import sanitize_value
        
        result = sanitize_value(["a", "b", "c"])
        self.assertEqual(result, "a, b, c")

    def test_sanitize_value_dict(self):
        """Санитизация словаря"""
        from src.utils.helpers import sanitize_value
        import json
        
        test_dict = {"key": "value"}
        result = sanitize_value(test_dict)
        parsed = json.loads(result)
        self.assertEqual(parsed, test_dict)

    def test_sanitize_value_datetime(self):
        """Санитизация datetime"""
        from src.utils.helpers import sanitize_value
        from datetime import datetime
        
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = sanitize_value(dt)
        self.assertIn("2024-01-15", result)


class TestChromeNotAvailableError(unittest.TestCase):
    """Тесты исключения ChromeNotAvailableError"""

    def test_exception_creation(self):
        """Создание исключения"""
        from src.clients.hackerone_scraper import ChromeNotAvailableError
        
        with self.assertRaises(ChromeNotAvailableError) as context:
            raise ChromeNotAvailableError("Chrome not found")
        
        self.assertIn("Chrome not found", str(context.exception))


class TestHackerTier(unittest.TestCase):
    """Тесты_enum HackerTier"""

    def test_tier_values(self):
        """Проверка значений тиров"""
        from src.models.entities import HackerTier
        
        self.assertEqual(HackerTier.NOVICE.value, "novice")
        self.assertEqual(HackerTier.STANDARD.value, "standard")
        self.assertEqual(HackerTier.PREMIUM.value, "premium")
        self.assertEqual(HackerTier.ELITE.value, "elite")


class TestReportState(unittest.TestCase):
    """Тесты_enum ReportState"""

    def test_state_values(self):
        """Проверка значений состояний"""
        from src.models.entities import ReportState
        
        self.assertEqual(ReportState.NEW.value, "new")
        self.assertEqual(ReportState.TRIAGED.value, "triaged")
        self.assertEqual(ReportState.RESOLVED.value, "resolved")
        self.assertEqual(ReportState.CLOSED.value, "closed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
