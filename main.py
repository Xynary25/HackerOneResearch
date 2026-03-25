#!/usr/bin/env python3
"""
HackerOne Research Tool

Сбор и анализ данных о багхантерах HackerOne для проектирования процессов
привлечения на платформу Standoff.

Использование:
    python main.py --limit 50 --reports 100
    python main.py --headless false
    python main.py --export json csv excel
    python main.py --category high_critical --limit 30
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import AppConfig
from src.clients.hackerone_scraper import HackerOneScraper, ChromeNotAvailableError
from src.collectors.data_collectors import LeaderboardCollector, HacktivityCollector
from src.processors.data_processors import DataNormalizer, DataEnricher, DataAggregator
from src.analyzers.data_analyzers import HackerAnalyzer, PortfolioAnalyzer
from src.exporters.data_exporters import JSONExporter, CSVExporter, ExcelExporter
from src.utils.helpers import setup_logging, print_header, print_table, create_directories
from src.models.entities import LeaderboardCategory


def parse_args():
    parser = argparse.ArgumentParser(
        description="HackerOne Research Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s --limit 20 --reports 30
  %(prog)s --headless false
  %(prog)s --export json csv excel
  %(prog)s --category high_critical --limit 30
        """
    )

    parser.add_argument("--limit", type=int, default=20, help="Лимит хакеров")
    parser.add_argument("--reports", type=int, default=30, help="Лимит отчётов")
    parser.add_argument("--headless", type=str, default="true",
                        choices=["true", "false"], help="Режим браузера")
    parser.add_argument("--export", nargs='+', default=["json", "csv"],
                        choices=["json", "csv", "excel"], help="Форматы экспорта")
    parser.add_argument("--output", type=str, default="data/processed",
                        help="Папка для результатов")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Уровень логирования")
    parser.add_argument("--category", type=str, default="reputation",
                        choices=["reputation", "high_critical", "owasp", "country", 
                                "asset_type", "up_and_comers", "upvotes"],
                        help="Категория лидерборда")
    parser.add_argument("--include-links", action="store_true", default=True,
                        help="Включить гиперссылки на профили в Excel")
    parser.add_argument("--use-advanced-rating", action="store_true", default=False,
                        help="Использовать расширенную формулу рейтинга")

    return parser.parse_args()


def main():
    args = parse_args()

    config = AppConfig()
    create_directories(config.base_dir)

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logger, log_file = setup_logging(config.logs_dir, log_level)

    headless = args.headless.lower() == "true"

    print_header("HACKERONE RESEARCH TOOL")
    print(f"СБОР ДАННЫХ ЧЕРЕЗ СКРАПИНГ")
    print(f"Соблюдайте условия использования HackerOne")
    print(f"\nЛог-файл: {log_file}\n")

    logger.info(f"Запуск: limit={args.limit}, reports={args.reports}, headless={headless}, category={args.category}")

    scraper = None

    try:
        print_header("1. ИНИЦИАЛИЗАЦИЯ")
        try:
            scraper = HackerOneScraper(headless=headless)
            print(f"Браузер инициализирован")
            logger.info("Браузер успешно инициализирован")
        except ChromeNotAvailableError as e:
            print(f"Ошибка: Google Chrome не найден")
            print(f"Установите Chrome: https://www.google.com/chrome/")
            print(f"\nДетали: {str(e)}")
            logger.error(f"Chrome не доступен: {e}")
            return
        except Exception as e:
            print(f"Ошибка инициализации: {str(e)}")
            logger.error(f"Ошибка инициализации: {e}", exc_info=True)
            return

        print_header("2. СБОР ДАННЫХ")
        leaderboard_collector = LeaderboardCollector(scraper)
        hacktivity_collector = HacktivityCollector(scraper)

        hackers = leaderboard_collector.collect(limit=args.limit, category=args.category)
        reports = hacktivity_collector.collect(limit=args.reports)

        print(f"Собрано хакеров: {len(hackers)}")
        print(f"Собрано отчётов: {len(reports)}")

        logger.info(f"Собрано хакеров: {len(hackers)}, отчётов: {len(reports)}")

        if len(hackers) == 0:
            print(f"\nНе удалось собрать данные!")
            print(f"Проверьте подключение и наличие Chrome")
            print(f"\nЛоги: {log_file}")
            logger.error("Не удалось собрать данные")
            return

        print_header("3. ОБРАБОТКА ДАННЫХ")
        try:
            normalizer = DataNormalizer(config)
            enricher = DataEnricher(config)

            hackers = normalizer.normalize(hackers)
            hackers = enricher.enrich(hackers)
            print(f"Нормализовано: {len(hackers)}")
            print(f"Обогащено метриками")
            logger.info(f"Обработано {len(hackers)} профилей")
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}", exc_info=True)
            print(f"Ошибка обработки: {str(e)}")

        print_header("4. АНАЛИЗ")
        try:
            analyzer = HackerAnalyzer()
            portfolio_analyzer = PortfolioAnalyzer()

            analyses = analyzer.analyze_batch(hackers)
            skills_dist = portfolio_analyzer.analyze_specialization(hackers)
            tier_dist = DataAggregator.aggregate_by_tier(hackers)
            stats = DataAggregator.calculate_stats(hackers)

            print(f"Проанализировано: {len(analyses)}")
            print(f"Распределение по тирам: {tier_dist}")
            print(f"Средний value_score: {stats.get('avg_value_score', 0)}")
            logger.info(f"Анализ завершён. Tier distribution: {tier_dist}")
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}", exc_info=True)
            print(f"Ошибка анализа: {str(e)}")
            analyses = []
            skills_dist = {}
            tier_dist = {}
            stats = {}

        print_header("5. ЭКСПОРТ")
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exported_files = []

        try:
            hackers_data = [h.to_dict() for h in hackers] if hackers else []
            analyses_data = [a.to_dict() for a in analyses] if analyses else []
            reports_data = [r.to_dict() for r in reports] if reports else []

            if "json" in args.export:
                json_exporter = JSONExporter(output_dir)
                with json_exporter:
                    if hackers_data:
                        exported_files.append(json_exporter.export(hackers_data, f"hackers_{timestamp}"))
                    if analyses_data:
                        exported_files.append(json_exporter.export(analyses_data, f"analyses_{timestamp}"))
                    if reports_data:
                        exported_files.append(json_exporter.export(reports_data, f"reports_{timestamp}"))

            if "csv" in args.export:
                csv_exporter = CSVExporter(output_dir)
                with csv_exporter:
                    if hackers_data:
                        exported_files.append(csv_exporter.export(hackers_data, f"hackers_{timestamp}"))
                    if analyses_data:
                        exported_files.append(csv_exporter.export(analyses_data, f"analyses_{timestamp}"))
                    if reports_data:
                        exported_files.append(csv_exporter.export(reports_data, f"reports_{timestamp}"))

            if "excel" in args.export:
                excel_exporter = ExcelExporter(output_dir)
                with excel_exporter:
                    if hackers_data:
                        exported_files.append(excel_exporter.export(hackers_data, f"hackers_{timestamp}", 
                                                                   link_column="profile_url" if args.include_links else None))
                    if analyses_data:
                        exported_files.append(excel_exporter.export(analyses_data, f"analyses_{timestamp}", link_column=None))

            print(f"Экспортировано файлов: {len(exported_files)}")
            for f in exported_files:
                print(f"  {f}")
                logger.info(f"Экспорт: {f}")
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}", exc_info=True)
            print(f"Ошибка экспорта: {str(e)}")

        print_header("6. РЕЗУЛЬТАТЫ")
        if analyses:
            headers = ["Username", "Tier", "Value", "Activity", "Priority"]
            rows = [[a.username, a.tier.value, a.value_score, a.activity_score, a.recruitment_priority]
                    for a in analyses[:10]]
            print_table(headers, rows)
        else:
            print(f"Нет данных анализа")

        print_header("7. РЕКОМЕНДАЦИИ")
        elite_count = tier_dist.get("elite", 0) if tier_dist else 0
        premium_count = tier_dist.get("premium", 0) if tier_dist else 0

        if elite_count > 0:
            print(f"Priority Recruitment: {elite_count} Elite")
        if premium_count > 0:
            print(f"Standard Recruitment: {premium_count} Premium")
        if skills_dist:
            print(f"Skills Focus: {list(skills_dist.keys())[:3]}")

        logger.info(f"Рекомендации: Elite={elite_count}, Premium={premium_count}")

        print_header("8. ВЫВОДЫ")
        print(f"Всего хакеров: {len(hackers)}")
        print(f"Elite/Premium: {elite_count}/{premium_count}")
        print(f"Средний Value Score: {stats.get('avg_value_score', 0) if stats else 0}")
        print(f"Отчётов проанализировано: {len(reports)}")
        print(f"\nЛог-файл: {log_file}")

    except KeyboardInterrupt:
        logger.warning("Прервано пользователем")
        print(f"\nРабота прервана")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)
        print(f"\nОшибка: {str(e)}")
        print(f"Логи: {log_file}")
        sys.exit(1)
    finally:
        if scraper:
            try:
                scraper.close()
                logger.info("Браузер закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии: {e}")

        print_header("ЗАВЕРШЕНО")
        print(f"Логи: {config.logs_dir}")


if __name__ == "__main__":
    main()