#!/usr/bin/env python3
"""
HackerOne Research Tool v3.0
Сбор и анализ данных о багхантерах HackerOne
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import argparse
import logging
from datetime import datetime
from colorama import Fore, Style, init
from src.config.settings import AppConfig
from src.clients.hackerone_scraper import HackerOneScraper
from src.collectors.data_collectors import LeaderboardCollector, HacktivityCollector
from src.processors.data_processors import DataNormalizer, DataEnricher, DataAggregator
from src.analyzers.data_analyzers import HackerAnalyzer, PortfolioAnalyzer
from src.exporters.data_exporters import JSONExporter, CSVExporter, ExcelExporter
from src.utils.helpers import setup_logging, print_header, print_table, create_directories

init()

CATEGORIES_DISPLAY = {
    "reputation": "🏆 По репутации",
    "high_critical": "🔴 High/Critical уязвимости",
    "owasp": "🛡️ OWASP Top 10",
    "country": "🌍 По странам",
    "asset_type": "💻 По типу активов",
    "up_and_comers": "📈 Восходящие звёзды",
    "upvotes": "👍 По голосам"
}


def get_user_input():
    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔍 НАСТРОЙКИ ЗАПУСКА{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}1. Категория лидерборда:{Style.RESET_ALL}")
    for i, (key, desc) in enumerate(CATEGORIES_DISPLAY.items(), 1):
        print(f"   [{i}] {desc}")
    while True:
        cat_choice = input(f"\n{Fore.GREEN}Выберите категорию (1-7, по умолчанию 1): {Style.RESET_ALL}").strip()
        if cat_choice in ['', '1']:
            category = "reputation"
            break
        try:
            cat_idx = int(cat_choice) - 1
            if 0 <= cat_idx < len(CATEGORIES_DISPLAY):
                category = list(CATEGORIES_DISPLAY.keys())[cat_idx]
                break
            else:
                print(f"{Fore.RED}❌ Число должно быть от 1 до 7{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ Введите число!{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}2. Режим браузера:{Style.RESET_ALL}")
    print("   [1] Headless (без окна, быстрее)")
    print("   [2] С окном браузера (видно процесс)")
    while True:
        browser_choice = input(f"\n{Fore.GREEN}Выберите режим (1-2, по умолчанию 1): {Style.RESET_ALL}").strip()
        if browser_choice in ['', '1']:
            headless = True
            break
        elif browser_choice == '2':
            headless = False
            break
        else:
            print(f"{Fore.RED}❌ Неверный ввод! Введите 1 или 2{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}3. Лимит хакеров:{Style.RESET_ALL}")
    print("   Диапазон: 5-100 (по умолчанию 20)")
    while True:
        hackers_input = input(f"{Fore.GREEN}Введите количество (5-100): {Style.RESET_ALL}").strip()
        if hackers_input == '':
            limit = 20
            break
        try:
            limit = int(hackers_input)
            if 5 <= limit <= 100:
                break
            else:
                print(f"{Fore.RED}❌ Число должно быть от 5 до 100{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ Введите число!{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}4. Лимит отчётов:{Style.RESET_ALL}")
    print("   Диапазон: 10-100 (по умолчанию 30)")
    while True:
        reports_input = input(f"{Fore.GREEN}Введите количество (10-100): {Style.RESET_ALL}").strip()
        if reports_input == '':
            reports = 30
            break
        try:
            reports = int(reports_input)
            if 10 <= reports <= 100:
                break
            else:
                print(f"{Fore.RED}❌ Число должно быть от 10 до 100{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ Введите число!{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}5. Форматы экспорта:{Style.RESET_ALL}")
    print("   [1] JSON")
    print("   [2] CSV")
    print("   [3] Excel (XLSX)")
    print("   [4] Все форматы")
    while True:
        export_choice = input(f"\n{Fore.GREEN}Выберите формат (1-4, по умолчанию 4): {Style.RESET_ALL}").strip()
        if export_choice in ['', '4']:
            export_formats = ['json', 'csv', 'excel']
            break
        elif export_choice == '1':
            export_formats = ['json']
            break
        elif export_choice == '2':
            export_formats = ['csv']
            break
        elif export_choice == '3':
            export_formats = ['excel']
            break
        else:
            print(f"{Fore.RED}❌ Неверный ввод! Введите 1, 2, 3 или 4{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ Настройки подтверждены:{Style.RESET_ALL}")
    print(f"   • Категория: {CATEGORIES_DISPLAY.get(category, category)}")
    print(f"   • Режим браузера: {'Headless' if headless else 'С окном'}")
    print(f"   • Лимит хакеров: {limit}")
    print(f"   • Лимит отчётов: {reports}")
    print(f"   • Форматы экспорта: {', '.join(export_formats).upper()}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
    return {
        'category': category,
        'headless': headless,
        'limit': limit,
        'reports': reports,
        'export': export_formats
    }


def main():
    parser = argparse.ArgumentParser(description="🔍 HackerOne Research Tool - Сбор и анализ данных")
    parser.add_argument("--category", type=str, default=None, choices=list(CATEGORIES_DISPLAY.keys()), help="Категория лидерборда")
    parser.add_argument("--limit", type=int, default=None, help="Количество хакеров (5-100)")
    parser.add_argument("--reports", type=int, default=None, help="Количество отчётов (10-100)")
    parser.add_argument("--headless", type=str, default=None, choices=['true', 'false'], help="Режим браузера")
    parser.add_argument("--export", nargs='+', choices=['json', 'csv', 'excel'], default=None, help="Форматы экспорта")
    parser.add_argument("--interactive", action="store_true", help="Интерактивный режим")
    parser.add_argument("--debug", action="store_true", help="Режим отладки")
    args = parser.parse_args()

    config = AppConfig()
    create_directories(config.base_dir)

    if args.interactive or (args.category is None and args.limit is None and args.headless is None):
        settings = get_user_input()
    else:
        settings = {
            'category': args.category if args.category else 'reputation',
            'headless': args.headless != 'false' if args.headless else True,
            'limit': args.limit if args.limit else 20,
            'reports': args.reports if args.reports else 30,
            'export': args.export if args.export else ['json', 'csv', 'excel']
        }

    settings['limit'] = max(5, min(100, settings['limit']))
    settings['reports'] = max(10, min(100, settings['reports']))

    log_level = logging.DEBUG if args.debug else logging.INFO
    logger, log_file_path = setup_logging(config.logs_dir, log_level)

    print_header("🔍 HACKERONE RESEARCH TOOL v3.0")
    print(f"{Fore.CYAN}📊 СБОР ДАННЫХ ЧЕРЕЗ СКРАПИНГ/ПАРСИНГ{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚠ Соблюдайте условия использования HackerOne{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚠ Rate limiting включён для защиты от блокировок{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}📁 Лог-файл: {log_file_path}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}🌐 Режим браузера: {'Headless' if settings['headless'] else 'С окном'}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}📊 Категория: {CATEGORIES_DISPLAY.get(settings['category'], settings['category'])}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}📊 Лимит хакеров: {settings['limit']}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}📰 Лимит отчётов: {settings['reports']}{Style.RESET_ALL}\n")

    logger.info(f"Запуск: category={settings['category']}, limit={settings['limit']}, reports={settings['reports']}, headless={settings['headless']}")
    scraper = None
    try:
        scraper = HackerOneScraper(headless=settings['headless'])

        print_header("1. СБОР ДАННЫХ")
        leaderboard_collector = LeaderboardCollector(scraper)
        hacktivity_collector = HacktivityCollector(scraper)
        hackers = leaderboard_collector.collect(limit=settings['limit'], category=settings['category'])
        reports = hacktivity_collector.collect(limit=settings['reports'])
        print(f"{Fore.GREEN}✓ Собрано хакеров: {len(hackers)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Собрано отчётов: {len(reports)}{Style.RESET_ALL}")
        logger.info(f"Собрано хакеров: {len(hackers)}, отчётов: {len(reports)}")

        if len(hackers) == 0:
            print(f"\n{Fore.RED}⚠ Не удалось собрать данные!{Style.RESET_ALL}")
            logger.error("Не удалось собрать данные — лидерборд пуст")
            return

        print_header("2. ОБРАБОТКА ДАННЫХ")
        normalizer = DataNormalizer(config)
        enricher = DataEnricher(config)
        hackers = normalizer.normalize(hackers)
        hackers = enricher.enrich(hackers)
        print(f"{Fore.GREEN}✓ Нормализовано: {len(hackers)}{Style.RESET_ALL}")
        logger.info(f"Обработано {len(hackers)} профилей")

        print_header("3. АНАЛИЗ")
        analyzer = HackerAnalyzer()
        portfolio_analyzer = PortfolioAnalyzer()
        analyses = analyzer.analyze_batch(hackers)
        skills_dist = portfolio_analyzer.analyze_specialization(hackers)
        tier_dist = DataAggregator.aggregate_by_tier(hackers)
        stats = DataAggregator.calculate_stats(hackers)
        print(f"{Fore.GREEN}✓ Проанализировано: {len(analyses)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Распределение по тирам: {tier_dist}{Style.RESET_ALL}")
        logger.info(f"Анализ завершён. Tier distribution: {tier_dist}")

        print_header("4. ЭКСПОРТ")
        output_dir = config.data_dir / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        hackers_data = [h.to_dict() for h in hackers]
        analyses_data = [a.to_dict() for a in analyses]
        reports_data = [r.to_dict() for r in reports]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exported_files = []

        if "json" in settings['export']:
            json_exporter = JSONExporter(output_dir)
            if hackers_data:
                exported_files.append(json_exporter.export(hackers_data, f"hackers_{timestamp}"))
            if analyses_data:
                exported_files.append(json_exporter.export(analyses_data, f"analyses_{timestamp}"))
            if reports_data:
                exported_files.append(json_exporter.export(reports_data, f"reports_{timestamp}"))

        if "csv" in settings['export']:
            csv_exporter = CSVExporter(output_dir)
            if hackers_data:
                exported_files.append(csv_exporter.export(hackers_data, f"hackers_{timestamp}"))
            if analyses_data:
                exported_files.append(csv_exporter.export(analyses_data, f"analyses_{timestamp}"))
            if reports_data:
                exported_files.append(csv_exporter.export(reports_data, f"reports_{timestamp}"))

        if "excel" in settings['export']:
            excel_exporter = ExcelExporter(output_dir)
            if hackers_data:
                exported_files.append(excel_exporter.export(hackers_data, f"hackers_{timestamp}"))
            if analyses_data:
                exported_files.append(excel_exporter.export(analyses_data, f"analyses_{timestamp}"))
            if reports_data:
                exported_files.append(excel_exporter.export(reports_data, f"reports_{timestamp}"))

        print(f"{Fore.GREEN}✓ Экспортировано файлов: {len(exported_files)}{Style.RESET_ALL}")
        for f in exported_files:
            print(f"  📁 {f}")
        logger.info(f"Экспорт: {exported_files}")

        print_header("5. РЕЗУЛЬТАТЫ")
        headers = ["Username", "Rank", "Tier", "Value", "Rep", "Signal", "Impact", "Priority"]
        rows = [[a.username, h.rank, a.tier.value, a.value_score, h.reputation, h.signal, h.impact, a.recruitment_priority]
                for h, a in list(zip(hackers, analyses))[:10]]
        print_table(headers, rows)

        print_header("6. РЕКОМЕНДАЦИИ ДЛЯ STANDOFF")
        elite_count = tier_dist.get("elite", 0)
        premium_count = tier_dist.get("premium", 0)
        standard_count = tier_dist.get("standard", 0)
        if elite_count > 0:
            print(f"{Fore.GREEN}✓ Priority Recruitment: {elite_count} Elite хакеров{Style.RESET_ALL}")
        if premium_count > 0:
            print(f"{Fore.YELLOW}✓ Standard Recruitment: {premium_count} Premium хакеров{Style.RESET_ALL}")
        if standard_count > 0:
            print(f"{Fore.CYAN}✓ Monitor: {standard_count} Standard хакеров{Style.RESET_ALL}")
        if skills_dist:
            print(f"{Fore.BLUE}✓ Skills Focus: {list(skills_dist.keys())[:3]}{Style.RESET_ALL}")
        logger.info(f"Рекомендации: Elite={elite_count}, Premium={premium_count}, Standard={standard_count}")

        print_header("7. ВЫВОДЫ")
        print(f"📊 Всего хакеров в выборке: {len(hackers)}")
        print(f"📊 Elite/Premium/Standard: {elite_count}/{premium_count}/{standard_count}")
        print(f"📊 Средний Value Score: {stats.get('avg_value_score', 0)}")
        print(f"📊 Отчётов проанализировано: {len(reports)}")
        print(f"\n{Fore.GREEN}📁 Лог-файл для отчёта об ошибках: {log_file_path}{Style.RESET_ALL}")

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Прервано пользователем{Style.RESET_ALL}")
        logger.warning("Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}", exc_info=True)
        print(f"\n{Fore.RED}❌ Произошла ошибка: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📁 Полные логи ошибки: {log_file_path}{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        if scraper:
            scraper.close()
        print_header("✅ ЗАВЕРШЕНО")
        print(f"{Fore.GREEN}📁 Логи сохранены в: {config.logs_dir}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()