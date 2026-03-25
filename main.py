#!/usr/bin/env python3
"""
HackerOne Research Tool - CLI версия
ИСПРАВЛЕНО: Правильный вызов setup_logging
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Добавляем корень проекта в path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import AppConfig
from src.clients.hackerone_scraper import HackerOneScraper
from src.collectors.data_collectors import LeaderboardCollector, HacktivityCollector
from src.processors.data_processors import DataNormalizer, DataEnricher, DataAggregator
from src.analyzers.data_analyzers import HackerAnalyzer, PortfolioAnalyzer
from src.exporters.data_exporters import JSONExporter, CSVExporter
from src.utils.helpers import setup_logging, print_header, print_table, create_directories


def parse_args():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="🔍 HackerOne Research Tool - Сбор и анализ данных",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --limit 20 --reports 30
  %(prog)s --headless false
  %(prog)s --export json csv
        """
    )

    # Настройки сбора
    parser.add_argument("--limit", type=int, default=20, help="Лимит хакеров")
    parser.add_argument("--reports", type=int, default=30, help="Лимит отчётов")
    parser.add_argument("--headless", type=str, default="true",
                        choices=["true", "false"], help="Запуск браузера в фоне")

    # Настройки экспорта
    parser.add_argument("--export", nargs='+', default=["json", "csv"],
                        choices=["json", "csv"], help="Форматы экспорта")
    parser.add_argument("--output", type=str, default="data/processed",
                        help="Папка для сохранения результатов")

    # Логирование
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Уровень логирования")

    return parser.parse_args()


def main():
    """Точка входа CLI"""
    args = parse_args()

    # Инициализация конфигурации
    config = AppConfig()
    create_directories(config.base_dir)

    # ✅ ИСПРАВЛЕНО: Передаём Path объект, а не строку
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    log_file = setup_logging(config.logs_dir, log_level)

    logger = logging.getLogger(__name__)
    headless = args.headless.lower() == "true"

    print_header("🔍 HACKERONE RESEARCH TOOL v3.0")
    print(f"{Fore.CYAN}📊 СБОР ДАННЫХ ЧЕРЕЗ СКРАПИНГ/ПАРСИНГ{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚠ Соблюдайте условия использования HackerOne{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚠ Rate limiting включён для защиты от блокировок{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}📁 Лог-файл: {log_file}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}📁 Папка логов: {config.logs_dir}{Style.RESET_ALL}\n")

    logger.info(f"Запуск: limit={args.limit}, reports={args.reports}, headless={headless}")

    scraper = None

    try:
        # 1. Инициализация скрапера
        scraper = HackerOneScraper(headless=headless)

        # 2. Сбор данных
        print_header("1. СБОР ДАННЫХ")
        leaderboard_collector = LeaderboardCollector(scraper)
        hacktivity_collector = HacktivityCollector(scraper)

        hackers = leaderboard_collector.collect(limit=args.limit)
        reports = hacktivity_collector.collect(limit=args.reports)

        print(f"{Fore.GREEN}✓ Собрано хакеров: {len(hackers)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Собрано отчётов: {len(reports)}{Style.RESET_ALL}")

        logger.info(f"Собрано хакеров: {len(hackers)}, отчётов: {len(reports)}")

        if len(hackers) == 0:
            print(f"\n{Fore.RED}⚠ Не удалось собрать данные!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Проверьте:{Style.RESET_ALL}")
            print("  - Подключение к интернету")
            print("  - Доступность hackerone.com")
            print("  - Установленный Google Chrome")
            print(f"\n{Fore.YELLOW}📁 Полные логи: {log_file}{Style.RESET_ALL}")
            logger.error("Не удалось собрать данные — лидерборд пуст")
            return

        # 3. Обработка
        print_header("2. ОБРАБОТКА ДАННЫХ")
        normalizer = DataNormalizer(config)
        enricher = DataEnricher(config)

        hackers = normalizer.normalize(hackers)
        hackers = enricher.enrich(hackers)
        print(f"{Fore.GREEN}✓ Нормализовано: {len(hackers)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Обогащено метриками{Style.RESET_ALL}")

        logger.info(f"Обработано {len(hackers)} профилей")

        # 4. Анализ
        print_header("3. АНАЛИЗ")
        analyzer = HackerAnalyzer()
        portfolio_analyzer = PortfolioAnalyzer()

        analyses = analyzer.analyze_batch(hackers)
        skills_dist = portfolio_analyzer.analyze_specialization(hackers)
        tier_dist = DataAggregator.aggregate_by_tier(hackers)
        stats = DataAggregator.calculate_stats(hackers)

        print(f"{Fore.GREEN}✓ Проанализировано: {len(analyses)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Распределение по тирам: {tier_dist}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Средний value_score: {stats.get('avg_value_score', 0)}{Style.RESET_ALL}")

        logger.info(f"Анализ завершён. Tier distribution: {tier_dist}")

        # 5. Экспорт
        print_header("4. ЭКСПОРТ")
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        hackers_data = [h.to_dict() for h in hackers]
        analyses_data = [a.to_dict() for a in analyses]
        reports_data = [r.to_dict() for r in reports]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exported_files = []

        if "json" in args.export:
            json_exporter = JSONExporter(output_dir)
            if hackers_data:
                exported_files.append(json_exporter.export(hackers_data, f"hackers_{timestamp}"))
            if analyses_data:
                exported_files.append(json_exporter.export(analyses_data, f"analyses_{timestamp}"))
            if reports_data:
                exported_files.append(json_exporter.export(reports_data, f"reports_{timestamp}"))

        if "csv" in args.export:
            csv_exporter = CSVExporter(output_dir)
            if hackers_data:
                exported_files.append(csv_exporter.export(hackers_data, f"hackers_{timestamp}"))
            if analyses_data:
                exported_files.append(csv_exporter.export(analyses_data, f"analyses_{timestamp}"))
            if reports_data:
                exported_files.append(csv_exporter.export(reports_data, f"reports_{timestamp}"))

        print(f"{Fore.GREEN}✓ Экспортировано файлов: {len(exported_files)}{Style.RESET_ALL}")
        for f in exported_files:
            print(f"  📁 {f}")
            logger.info(f"Экспорт: {f}")

        # 6. Результаты
        print_header("5. РЕЗУЛЬТАТЫ")
        headers = ["Username", "Tier", "Value", "Activity", "Priority"]
        rows = [[a.username, a.tier.value, a.value_score, a.activity_score, a.recruitment_priority]
                for a in analyses[:10]]
        print_table(headers, rows)

        # 7. Рекомендации
        print_header("6. РЕКОМЕНДАЦИИ ДЛЯ STANDOFF")
        elite_count = tier_dist.get("elite", 0)
        premium_count = tier_dist.get("premium", 0)

        if elite_count > 0:
            print(f"{Fore.GREEN}✓ Priority Recruitment: {elite_count} Elite хакеров{Style.RESET_ALL}")
        if premium_count > 0:
            print(f"{Fore.YELLOW}✓ Standard Recruitment: {premium_count} Premium хакеров{Style.RESET_ALL}")
        if skills_dist:
            print(f"{Fore.CYAN}✓ Skills Focus: {list(skills_dist.keys())[:3]}{Style.RESET_ALL}")

        logger.info(f"Рекомендации: Elite={elite_count}, Premium={premium_count}")

        # 8. Выводы
        print_header("7. ВЫВОДЫ")
        print(f"📊 Всего хакеров в выборке: {len(hackers)}")
        print(f"📊 Elite/Premium: {elite_count}/{premium_count}")
        print(f"📊 Средний Value Score: {stats.get('avg_value_score', 0)}")
        print(f"📊 Отчётов проанализировано: {len(reports)}")
        print(f"\n{Fore.GREEN}📁 Лог-файл для отчёта об ошибках: {log_file}{Style.RESET_ALL}")

    except KeyboardInterrupt:
        logger.warning("⚠ Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}", exc_info=True)
        print(f"\n{Fore.RED}❌ Произошла ошибка: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📁 Полные логи ошибки: {log_file}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Отправьте этот файл для диагностики{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        if scraper:
            scraper.close()

        print_header("✅ ЗАВЕРШЕНО")
        print(f"{Fore.GREEN}📁 Логи сохранены в: {config.logs_dir}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}📄 Последний лог: {log_file}{Style.RESET_ALL}")


if __name__ == "__main__":
    from colorama import Fore, Style

    main()