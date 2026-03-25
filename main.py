#!/usr/bin/env python3
"""
HackerOne Research Tool - CLI версия

Инструмент для сбора и анализа данных с платформы HackerOne.
Собирает данные о хакерах из лидерборда и Hacktivity, обрабатывает,
анализирует и экспортирует результаты в JSON/CSV форматы.

Пример использования:
    python main.py --limit 20 --reports 30 --export json csv

Автор: Security Research Team
Версия: 3.0
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Добавляем корень проекта в path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import AppConfig
from src.clients.hackerone_scraper import HackerOneScraper, ChromeNotAvailableError
from src.collectors.data_collectors import LeaderboardCollector, HacktivityCollector
from src.processors.data_processors import DataNormalizer, DataEnricher, DataAggregator
from src.analyzers.data_analyzers import HackerAnalyzer, PortfolioAnalyzer
from src.exporters.data_exporters import JSONExporter, CSVExporter
from src.utils.helpers import setup_logging, print_header, print_table, create_directories
from colorama import Fore, Style


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

    # Настройка логирования
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logger, log_file = setup_logging(config.logs_dir, log_level)

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
        # 1. Инициализация скрапера с обработкой отсутствия Chrome
        print_header("1. ИНИЦИАЛИЗАЦИЯ")
        try:
            scraper = HackerOneScraper(headless=headless)
            print(f"{Fore.GREEN}✓ Браузер инициализирован{Style.RESET_ALL}")
            logger.info("Браузер успешно инициализирован")
        except ChromeNotAvailableError as e:
            print(f"{Fore.RED}❌ Ошибка: Google Chrome не найден{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 Рекомендации:{Style.RESET_ALL}")
            print("  - Установите Google Chrome: https://www.google.com/chrome/")
            print("  - Или используйте режим без браузера (если поддерживается)")
            print(f"\n{Fore.CYAN}📄 Детали ошибки: {str(e)}{Style.RESET_ALL}")
            logger.error(f"Chrome не доступен: {e}")
            return
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка инициализации браузера: {str(e)}{Style.RESET_ALL}")
            logger.error(f"Ошибка инициализации браузера: {e}", exc_info=True)
            return

        # 2. Сбор данных
        print_header("2. СБОР ДАННЫХ")
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

        # 3. Обработка данных с обработкой ошибок
        print_header("3. ОБРАБОТКА ДАННЫХ")
        try:
            normalizer = DataNormalizer(config)
            enricher = DataEnricher(config)

            hackers = normalizer.normalize(hackers)
            hackers = enricher.enrich(hackers)
            print(f"{Fore.GREEN}✓ Нормализовано: {len(hackers)}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}✓ Обогащено метриками{Style.RESET_ALL}")
            logger.info(f"Обработано {len(hackers)} профилей")
        except Exception as e:
            logger.error(f"Ошибка обработки данных: {e}", exc_info=True)
            print(f"{Fore.RED}⚠ Ошибка обработки данных: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 Продолжаем с исходными данными{Style.RESET_ALL}")

        # 4. Анализ с обработкой ошибок
        print_header("4. АНАЛИЗ")
        try:
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
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}", exc_info=True)
            print(f"{Fore.RED}⚠ Ошибка анализа: {str(e)}{Style.RESET_ALL}")
            analyses = []
            skills_dist = {}
            tier_dist = {}
            stats = {}

        # 5. Экспорт с контекстными менеджерами и обработкой ошибок
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

            print(f"{Fore.GREEN}✓ Экспортировано файлов: {len(exported_files)}{Style.RESET_ALL}")
            for f in exported_files:
                print(f"  📁 {f}")
                logger.info(f"Экспорт: {f}")
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}", exc_info=True)
            print(f"{Fore.RED}⚠ Ошибка экспорта: {str(e)}{Style.RESET_ALL}")

        # 6. Результаты с обработкой пустых данных
        print_header("6. РЕЗУЛЬТАТЫ")
        if analyses:
            headers = ["Username", "Tier", "Value", "Activity", "Priority"]
            rows = [[a.username, a.tier.value, a.value_score, a.activity_score, a.recruitment_priority]
                    for a in analyses[:10]]
            print_table(headers, rows)
        else:
            print(f"{Fore.YELLOW}⚠ Нет данных анализа для отображения{Style.RESET_ALL}")

        # 7. Рекомендации
        print_header("7. РЕКОМЕНДАЦИИ ДЛЯ STANDOFF")
        elite_count = tier_dist.get("elite", 0) if tier_dist else 0
        premium_count = tier_dist.get("premium", 0) if tier_dist else 0

        if elite_count > 0:
            print(f"{Fore.GREEN}✓ Priority Recruitment: {elite_count} Elite хакеров{Style.RESET_ALL}")
        if premium_count > 0:
            print(f"{Fore.YELLOW}✓ Standard Recruitment: {premium_count} Premium хакеров{Style.RESET_ALL}")
        if skills_dist:
            print(f"{Fore.CYAN}✓ Skills Focus: {list(skills_dist.keys())[:3]}{Style.RESET_ALL}")

        logger.info(f"Рекомендации: Elite={elite_count}, Premium={premium_count}")

        # 8. Выводы
        print_header("8. ВЫВОДЫ")
        print(f"📊 Всего хакеров в выборке: {len(hackers)}")
        print(f"📊 Elite/Premium: {elite_count}/{premium_count}")
        print(f"📊 Средний Value Score: {stats.get('avg_value_score', 0) if stats else 0}")
        print(f"📊 Отчётов проанализировано: {len(reports)}")
        print(f"\n{Fore.GREEN}📁 Лог-файл для отчёта об ошибках: {log_file}{Style.RESET_ALL}")

    except KeyboardInterrupt:
        logger.warning("⚠ Прервано пользователем")
        print(f"\n{Fore.YELLOW}💡 Работа прервана. Данные могли быть сохранены частично.{Style.RESET_ALL}")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}", exc_info=True)
        print(f"\n{Fore.RED}❌ Произошла ошибка: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📁 Полные логи ошибки: {log_file}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Отправьте этот файл для диагностики{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        # Корректное закрытие ресурсов с обработкой ошибок
        if scraper:
            try:
                scraper.close()
                logger.info("Браузер корректно закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии браузера: {e}")

        print_header("✅ ЗАВЕРШЕНО")
        print(f"{Fore.GREEN}📁 Логи сохранены в: {config.logs_dir}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}📄 Последний лог: {log_file}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()