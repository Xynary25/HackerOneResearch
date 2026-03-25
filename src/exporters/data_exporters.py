import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

try:
    from openpyxl import Workbook

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logging.warning("openpyxl не установлен — Excel экспорт недоступен")

logger = logging.getLogger(__name__)


class JSONExporter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, data: List[Dict], filename: str) -> str:
        filepath = self.output_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"📁 Экспорт JSON: {filepath}")
        return str(filepath)


class CSVExporter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, data: List[Dict], filename: str) -> str:
        if not data:
            logger.warning("⚠ Нет данных для экспорта CSV")
            return ""
        filepath = self.output_dir / f"{filename}.csv"
        fieldnames = list(data[0].keys())
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"📁 Экспорт CSV: {filepath}")
        return str(filepath)


class ExcelExporter:
    """Экспорт в Excel с обработкой ошибок"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_value(self, value: Any) -> Any:
        """✅ ИСПРАВЛЕНО: Конвертация значений для Excel"""
        if value is None:
            return ""
        if isinstance(value, list):
            # Преобразуем список в строку
            return ", ".join(str(item) for item in value) if value else ""
        if isinstance(value, dict):
            # Преобразуем словарь в строку
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, (int, float, str, bool)):
            return value
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        # Для всех остальных типов - строковое представление
        return str(value)

    def export(self, data: List[Dict], filename: str) -> str:
        if not EXCEL_AVAILABLE:
            logger.warning("⚠ Excel экспорт недоступен — установите openpyxl")
            return ""

        if not data:
            logger.warning("⚠ Нет данных для экспорта Excel")
            return ""

        filepath = self.output_dir / f"{filename}.xlsx"

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "HackerOne Data"[:31]  # Excel ограничивает имя листа 31 символом

            # Заголовки
            headers = list(data[0].keys())
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=str(header))
                cell.font = cell.font.copy(bold=True)

            # Данные
            for row_idx, row_data in enumerate(data, 2):
                for col_idx, header in enumerate(headers, 1):
                    value = row_data.get(header, '')
                    # ✅ ИСПРАВЛЕНО: Санитизация значения перед записью
                    sanitized_value = self._sanitize_value(value)
                    cell = ws.cell(row=row_idx, column=col_idx, value=sanitized_value)

            # Авто-ширина колонок
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column].width = adjusted_width

            wb.save(filepath)
            logger.info(f"📁 Экспорт Excel: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта Excel: {e}")
            return ""


class ExportManager:
    def __init__(self, output_dir: Path, export_excel: bool = False):
        self.json_exporter = JSONExporter(output_dir)
        self.csv_exporter = CSVExporter(output_dir)
        self.excel_exporter = ExcelExporter(output_dir) if export_excel else None
        self.exported_files = []

    def export_all(self, hackers: List[Dict], analyses: List[Dict],
                   reports: List[Dict], formats: List[str] = None) -> List[str]:
        formats = formats or ["json", "csv"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Удаляем дубликаты по username
        hackers = self._remove_duplicates(hackers, 'username')
        analyses = self._remove_duplicates(analyses, 'username')
        reports = self._remove_duplicates(reports, 'report_id')

        if "json" in formats:
            if hackers:
                self.exported_files.append(self.json_exporter.export(hackers, f"hackers_{timestamp}"))
            if analyses:
                self.exported_files.append(self.json_exporter.export(analyses, f"analyses_{timestamp}"))
            if reports:
                self.exported_files.append(self.json_exporter.export(reports, f"reports_{timestamp}"))

        if "csv" in formats:
            if hackers:
                self.exported_files.append(self.csv_exporter.export(hackers, f"hackers_{timestamp}"))
            if analyses:
                self.exported_files.append(self.csv_exporter.export(analyses, f"analyses_{timestamp}"))
            if reports:
                self.exported_files.append(self.csv_exporter.export(reports, f"reports_{timestamp}"))

        if self.excel_exporter and "excel" in formats:
            if hackers:
                result = self.excel_exporter.export(hackers, f"hackers_{timestamp}")
                if result:
                    self.exported_files.append(result)
            if analyses:
                result = self.excel_exporter.export(analyses, f"analyses_{timestamp}")
                if result:
                    self.exported_files.append(result)

        return self.exported_files

    def _remove_duplicates(self, data: List[Dict], key: str) -> List[Dict]:
        """Удаление дубликатов по ключу"""
        seen = set()
        unique_data = []
        for item in data:
            identifier = item.get(key)
            if identifier and identifier not in seen:
                seen.add(identifier)
                unique_data.append(item)

        removed_count = len(data) - len(unique_data)
        if removed_count > 0:
            logger.info(f"🗑 Удалено {removed_count} дубликатов")

        return unique_data