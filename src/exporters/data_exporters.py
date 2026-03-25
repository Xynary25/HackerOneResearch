import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.hyperlink import Hyperlink

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logging.warning("openpyxl не установлен — Excel экспорт недоступен")

logger = logging.getLogger(__name__)


class JSONExporter:
    """Экспорт данных в формат JSON с поддержкой контекстного менеджера"""
    
    def __init__(self, output_dir: Path, indent: int = 2, ensure_ascii: bool = False):
        self.output_dir = output_dir
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._file_handle = None

    def export(self, data: List[Dict], filename: str) -> str:
        filepath = self.output_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=self.indent, ensure_ascii=self.ensure_ascii, default=str)
        logger.info(f"Export JSON: {filepath}")
        return str(filepath)

    def __enter__(self):
        """Контекстный менеджер: вход"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход"""
        pass


class CSVExporter:
    """Экспорт данных в формат CSV с поддержкой контекстного менеджера"""
    
    def __init__(self, output_dir: Path, delimiter: str = ","):
        self.output_dir = output_dir
        self.delimiter = delimiter
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._file_handle = None

    def export(self, data: List[Dict], filename: str) -> str:
        if not data:
            logger.warning("No data for CSV export")
            return ""
        filepath = self.output_dir / f"{filename}.csv"
        fieldnames = list(data[0].keys())
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Export CSV: {filepath}")
        return str(filepath)

    def __enter__(self):
        """Контекстный менеджер: вход"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход"""
        pass


class ExcelExporter:
    """Экспорт в Excel с гиперссылками на профили и авто-форматированием"""

    def __init__(self, output_dir: Path, auto_width: bool = True, max_column_width: int = 50):
        self.output_dir = output_dir
        self.auto_width = auto_width
        self.max_column_width = max_column_width
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.header_font = Font(bold=True, color="FFFFFF")
        self.header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        self.header_alignment = Alignment(horizontal="center", vertical="center")
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        self.cell_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    def _sanitize_value(self, value: Any) -> Any:
        """Конвертация значений для Excel"""
        if value is None:
            return ""
        if isinstance(value, list):
            return ", ".join(str(item) for item in value) if value else ""
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, (int, float, str, bool)):
            return value
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)

    def export(self, data: List[Dict], filename: str, link_column: Optional[str] = "profile_url") -> str:
        if not EXCEL_AVAILABLE:
            logger.warning("Excel export unavailable — install openpyxl")
            return ""

        if not data:
            logger.warning("No data for Excel export")
            return ""

        filepath = self.output_dir / f"{filename}.xlsx"

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "HackerOne Data"[:31]

            headers = list(data[0].keys())
            
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=str(header))
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.alignment = self.header_alignment

            link_col_idx = headers.index(link_column) + 1 if link_column in headers else None

            for row_idx, row_data in enumerate(data, 2):
                for col_idx, header in enumerate(headers, 1):
                    value = row_data.get(header, '')
                    sanitized_value = self._sanitize_value(value)
                    cell = ws.cell(row=row_idx, column=col_idx, value=sanitized_value)
                    cell.alignment = self.cell_alignment
                    
                    if link_col_idx and col_idx == link_col_idx and sanitized_value:
                        try:
                            cell.hyperlink = sanitized_value
                            cell.value = f"Profile Link"
                            cell.style = "Hyperlink"
                        except Exception:
                            pass

            if self.auto_width:
                for col in ws.columns:
                    max_length = 0
                    column = col[0].column_letter
                    for cell in col:
                        try:
                            if cell.value and len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except Exception:
                            pass
                    adjusted_width = min(max_length + 2, self.max_column_width)
                    ws.column_dimensions[column].width = adjusted_width

            wb.save(filepath)
            logger.info(f"Export Excel: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Excel export error: {e}")
            return ""


class ExportManager:
    def __init__(self, output_dir: Path, export_excel: bool = False, 
                 export_formats: List[str] = None, include_links: bool = True):
        self.output_dir = output_dir
        self.export_excel = export_excel
        self.export_formats = export_formats or ["json", "csv"]
        self.include_links = include_links
        
        self.json_exporter = JSONExporter(output_dir)
        self.csv_exporter = CSVExporter(output_dir)
        self.excel_exporter = ExcelExporter(output_dir) if export_excel else None
        self.exported_files = []

    def export_all(self, hackers: List[Dict], analyses: List[Dict],
                   reports: List[Dict], formats: List[str] = None) -> List[str]:
        formats = formats or self.export_formats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
                result = self.excel_exporter.export(hackers, f"hackers_{timestamp}", 
                                                    link_column="profile_url" if self.include_links else None)
                if result:
                    self.exported_files.append(result)
            if analyses:
                result = self.excel_exporter.export(analyses, f"analyses_{timestamp}", link_column=None)
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
            logger.info(f"Removed {removed_count} duplicates")

        return unique_data