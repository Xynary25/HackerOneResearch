import logging
import sys
import json
from pathlib import Path
from typing import List, Tuple, Any, Optional
from datetime import datetime, date
from colorama import init, Fore, Style

init()


def setup_logging(logs_dir: Path, level: int = logging.INFO) -> Tuple[logging.Logger, Path]:
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"hackerone_{timestamp}.log"

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info(f"Лог-файл создан: {log_file}")

    return logger, log_file


def print_header(title: str):
    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{title.center(60)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")


def print_table(headers: List[str], rows: List[List[str]]):
    if not rows:
        print("Нет данных для отображения")
        return

    col_widths = [max(len(str(item)) for item in col) for col in zip(headers, *rows)]
    header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))

    print(Fore.GREEN + header_row + Style.RESET_ALL)
    print("-" * len(header_row))

    for row in rows:
        print(" | ".join(str(item).ljust(w) for item, w in zip(row, col_widths)))


def create_directories(base_dir: Path):
    dirs = ["data/raw", "data/processed", "data/reports", "data/debug", "logs"]
    for d in dirs:
        (base_dir / d).mkdir(parents=True, exist_ok=True)


def sanitize_value(value: Any) -> Any:
    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, default=str)

    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(value, (int, float, str, bool)):
        return value

    return str(value)