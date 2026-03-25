#!/usr/bin/env python3
"""
Простой GUI для HackerOne Research Tool на Tkinter
ИСПРАВЛЕНО: Добавлен экспорт логов, исправлены ошибки Excel/settings
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем корень проекта в path для импортов
sys.path.insert(0, str(Path(__file__).parent))

from src.clients.hackerone_scraper import HackerOneScraper
from src.collectors.data_collectors import LeaderboardCollector, HacktivityCollector
from src.processors.data_processors import DataNormalizer, DataEnricher, DataAggregator
from src.analyzers.data_analyzers import HackerAnalyzer, PortfolioAnalyzer
from src.exporters.data_exporters import JSONExporter, CSVExporter, ExcelExporter
from src.config.settings import AppConfig
from src.utils.helpers import create_directories


class HackerOneGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 HackerOne Research Tool v3.0")
        self.root.geometry("800x650")
        self.root.resizable(False, False)

        # Настройки по умолчанию
        self.settings = {
            "limit": 20,
            "reports": 30,
            "headless": True,
            "export_json": True,
            "export_csv": True,
            "export_excel": False,  # ✅ ДОБАВЛЕНО
            "output_dir": "data/processed"
        }

        self.config = None
        self.running = False
        self.log_messages = []

        # Создаём директорию для логов
        self.logs_dir = Path(__file__).parent / 'logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self._setup_styles()
        self._create_widgets()

    def _setup_styles(self):
        """Настройка стилей интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Subheader.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Status.TLabel', foreground='blue')
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')

    def _create_widgets(self):
        """Создание виджетов интерфейса"""
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # === Заголовок ===
        header = ttk.Label(main_frame, text="🔍 HackerOne Research Tool",
                           style='Header.TLabel')
        header.grid(row=0, column=0, columnspan=3, pady=(0, 15))

        # === Настройки сбора ===
        ttk.Label(main_frame, text="📊 Настройки сбора:",
                  style='Subheader.TLabel').grid(row=1, column=0, sticky="w", pady=5)

        # Лимит хакеров
        ttk.Label(main_frame, text="Лимит хакеров:").grid(row=2, column=0, sticky="w")
        self.limit_var = tk.IntVar(value=self.settings["limit"])
        limit_spin = ttk.Spinbox(main_frame, from_=5, to=100,
                                 textvariable=self.limit_var, width=10)
        limit_spin.grid(row=2, column=1, sticky="w", padx=10)

        # Лимит отчётов
        ttk.Label(main_frame, text="Лимит отчётов:").grid(row=3, column=0, sticky="w")
        self.reports_var = tk.IntVar(value=self.settings["reports"])
        reports_spin = ttk.Spinbox(main_frame, from_=10, to=100,
                                   textvariable=self.reports_var, width=10)
        reports_spin.grid(row=3, column=1, sticky="w", padx=10)

        # Headless режим
        self.headless_var = tk.BooleanVar(value=self.settings["headless"])
        headless_check = ttk.Checkbutton(main_frame, text="Запуск в фоне (headless)",
                                         variable=self.headless_var)
        headless_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

        # === Настройки экспорта ===
        ttk.Label(main_frame, text="📁 Настройки экспорта:",
                  style='Subheader.TLabel').grid(row=5, column=0, sticky="w", pady=(15, 5))

        # Экспорт форматы
        self.export_json_var = tk.BooleanVar(value=self.settings["export_json"])
        self.export_csv_var = tk.BooleanVar(value=self.settings["export_csv"])
        self.export_excel_var = tk.BooleanVar(value=self.settings["export_excel"])  # ✅ Теперь работает

        json_check = ttk.Checkbutton(main_frame, text="Экспорт в JSON",
                                     variable=self.export_json_var)
        json_check.grid(row=6, column=0, sticky="w")

        csv_check = ttk.Checkbutton(main_frame, text="Экспорт в CSV",
                                    variable=self.export_csv_var)
        csv_check.grid(row=6, column=1, sticky="w")

        excel_check = ttk.Checkbutton(main_frame, text="Экспорт в Excel",
                                      variable=self.export_excel_var)
        excel_check.grid(row=6, column=2, sticky="w")

        # Папка вывода
        ttk.Label(main_frame, text="Папка вывода:").grid(row=7, column=0, sticky="w", pady=(10, 0))
        self.output_var = tk.StringVar(value=self.settings["output_dir"])
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=35)
        output_entry.grid(row=8, column=0, columnspan=2, sticky="we", padx=(0, 5))

        browse_btn = ttk.Button(main_frame, text="Обзор...",
                                command=self._browse_folder)
        browse_btn.grid(row=8, column=2, sticky="e")

        # === Статус ===
        ttk.Label(main_frame, text="Статус:", style='Subheader.TLabel').grid(
            row=9, column=0, sticky="w", pady=(20, 5))

        self.status_var = tk.StringVar(value="Готов к запуску")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var,
                                      style='Status.TLabel', wraplength=600)
        self.status_label.grid(row=10, column=0, columnspan=3, sticky="w")

        # Прогресс бар
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=11, column=0, columnspan=3, sticky="we", pady=5)

        # === Кнопки управления ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=12, column=0, columnspan=3, pady=15)

        run_btn = ttk.Button(btn_frame, text="▶ Запустить сбор",
                             command=self._start_collection)
        run_btn.pack(side="left", padx=5)

        stop_btn = ttk.Button(btn_frame, text="⏹ Остановить",
                              command=self._stop_collection, state="disabled")
        self.stop_btn = stop_btn
        stop_btn.pack(side="left", padx=5)

        clear_btn = ttk.Button(btn_frame, text="🗑 Очистить лог",
                               command=self._clear_log)
        clear_btn.pack(side="left", padx=5)

        # ✅ Кнопка экспорта логов
        export_log_btn = ttk.Button(btn_frame, text="📥 Экспорт логов",
                                    command=self._export_logs)
        export_log_btn.pack(side="left", padx=5)

        # === Лог вывода ===
        ttk.Label(main_frame, text="📋 Лог выполнения:",
                  style='Subheader.TLabel').grid(row=13, column=0, sticky="w")

        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=14, column=0, columnspan=3, sticky="nsew")

        self.log_text = tk.Text(log_frame, height=12, width=80,
                                font=('Consolas', 9), state='disabled')
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # === Нижняя панель ===
        footer = ttk.Frame(main_frame)
        footer.grid(row=15, column=0, columnspan=3, pady=(15, 0))

        ttk.Label(footer, text="© 2026 HackerOne Research Tool").pack(side="left")

        # Разрешаем растягивание
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _browse_folder(self):
        """Открыть диалог выбора папки"""
        folder = filedialog.askdirectory(initialdir="data/processed")
        if folder:
            self.output_var.set(folder)

    def _log(self, message, level="info"):
        """Добавить сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        self.log_messages.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })

        self.log_text.configure(state='normal')
        colors = {"info": "black", "success": "green", "error": "red", "warning": "orange"}
        self.log_text.insert("end", f"{log_entry}\n", colors.get(level, "black"))
        self.log_text.see("end")
        self.log_text.configure(state='disabled')

    def _export_logs(self):
        """✅ Экспорт логов в файл"""
        if not self.log_messages:
            messagebox.showinfo("Информация", "Лог пуст — нет данных для экспорта")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"hackerone_log_{timestamp}.json"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=default_filename,
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Сохранить лог"
        )

        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({
                        "exported_at": datetime.now().isoformat(),
                        "total_messages": len(self.log_messages),
                        "logs": self.log_messages
                    }, f, indent=2, ensure_ascii=False)

                self._log(f"✓ Лог экспортирован: {filepath}", "success")
                messagebox.showinfo("Успех",
                                    f"Лог сохранён:\n{filepath}\n\nТеперь вы можете отправить этот файл для диагностики")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить лог:\n{str(e)}")
                self._log(f"❌ Ошибка экспорта лога: {e}", "error")

    def _update_status(self, message, style='Status.TLabel'):
        """Обновить статус"""
        self.status_var.set(message)
        self.status_label.configure(style=style)

    def _start_collection(self):
        """Запустить сбор данных в отдельном потоке"""
        if self.running:
            return

        # Валидация: хотя бы один формат экспорта
        if not any([self.export_json_var.get(), self.export_csv_var.get(), self.export_excel_var.get()]):
            messagebox.showwarning("Предупреждение",
                                   "Выберите хотя бы один формат экспорта!")
            return

        # Обновление настроек
        self.settings.update({
            "limit": self.limit_var.get(),
            "reports": self.reports_var.get(),
            "headless": self.headless_var.get(),
            "export_json": self.export_json_var.get(),
            "export_csv": self.export_csv_var.get(),
            "export_excel": self.export_excel_var.get(),  # ✅ ДОБАВЛЕНО
            "output_dir": self.output_var.get()
        })

        # Блокировка интерфейса
        self.running = True
        self.progress.start(10)
        self._update_status("Инициализация...", 'Status.TLabel')
        self.stop_btn.configure(state="normal")
        self._log(f"Запуск с настройками: limit={self.settings['limit']}, reports={self.settings['reports']}", "info")

        # Запуск в фоне
        thread = threading.Thread(target=self._run_pipeline, daemon=True)
        thread.start()

    def _run_pipeline(self):
        """Основной пайплайн сбора и обработки"""
        try:
            # 1. Инициализация конфигурации
            self._update_status("Загрузка конфигурации...", 'Status.TLabel')
            self._log("Инициализация AppConfig...", "info")
            self.config = AppConfig()
            create_directories(self.config.base_dir)

            # 2. Инициализация скрапера
            self._update_status("Запуск браузера...", 'Status.TLabel')
            self._log("Инициализация HackerOneScraper...", "info")

            scraper = HackerOneScraper(headless=self.settings["headless"])

            # 3. Сбор данных
            self._update_status("Сбор лидерборда...", 'Status.TLabel')
            leaderboard_collector = LeaderboardCollector(scraper)

            hackers = leaderboard_collector.collect(limit=self.settings["limit"])
            self._log(f"✓ Собрано {len(hackers)} профилей", "success")

            self._update_status("Сбор hacktivity...", 'Status.TLabel')
            hacktivity_collector = HacktivityCollector(scraper)

            reports = hacktivity_collector.collect(limit=self.settings["reports"])
            self._log(f"✓ Собрано {len(reports)} отчётов", "success")

            # 4. Обработка
            self._update_status("Обработка данных...", 'Status.TLabel')
            normalizer = DataNormalizer(self.config)
            enricher = DataEnricher(self.config)

            hackers = normalizer.normalize(hackers)
            hackers = enricher.enrich(hackers)
            self._log("✓ Данные нормализованы и обогащены", "success")

            # 5. Анализ
            self._update_status("Анализ и скоринг...", 'Status.TLabel')
            analyzer = HackerAnalyzer()
            portfolio_analyzer = PortfolioAnalyzer()

            analyses = analyzer.analyze_batch(hackers)
            tier_dist = DataAggregator.aggregate_by_tier(hackers)
            stats = DataAggregator.calculate_stats(hackers)

            self._log(f"✓ Распределение по тирам: {tier_dist}", "info")

            # 6. Экспорт
            self._update_status("Экспорт результатов...", 'Status.TLabel')
            output_dir = Path(self.settings["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)

            hackers_data = [h.to_dict() for h in hackers]
            analyses_data = [a.to_dict() for a in analyses]
            reports_data = [r.to_dict() for r in reports]

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            exported_files = []

            # ✅ ИСПРАВЛЕННАЯ ЛОГИКА ЭКСПОРТА
            if self.export_json_var.get():
                json_exporter = JSONExporter(output_dir)
                if hackers_data:
                    exported_files.append(json_exporter.export(hackers_data, f"hackers_{timestamp}"))
                if analyses_data:
                    exported_files.append(json_exporter.export(analyses_data, f"analyses_{timestamp}"))
                if reports_data:
                    exported_files.append(json_exporter.export(reports_data, f"reports_{timestamp}"))

            if self.export_csv_var.get():
                csv_exporter = CSVExporter(output_dir)
                if hackers_data:
                    exported_files.append(csv_exporter.export(hackers_data, f"hackers_{timestamp}"))
                if analyses_data:
                    exported_files.append(csv_exporter.export(analyses_data, f"analyses_{timestamp}"))
                if reports_data:
                    exported_files.append(csv_exporter.export(reports_data, f"reports_{timestamp}"))

            if self.export_excel_var.get():  # ✅ ИСПРАВЛЕНО: было self.settings["export_json"]
                excel_exporter = ExcelExporter(output_dir)
                if hackers_data:
                    exported_files.append(excel_exporter.export(hackers_data, f"hackers_{timestamp}"))
                if analyses_data:
                    exported_files.append(excel_exporter.export(analyses_data, f"analyses_{timestamp}"))

            self._log(f"✓ Экспортировано {len(exported_files)} файлов", "success")
            for f in exported_files:
                self._log(f"  📁 {f}", "info")

            # 7. Показ результатов
            self._show_results(hackers, analyses, tier_dist, stats)

            # 8. Завершение
            scraper.close()
            self._update_status("✅ Завершено успешно!", 'Success.TLabel')
            self._log("🎉 Все операции завершены", "success")

        except Exception as e:
            self._log(f"❌ Ошибка: {str(e)}", "error")
            self._update_status("❌ Ошибка выполнения", 'Error.TLabel')
            import traceback
            self._log(traceback.format_exc(), "error")

        finally:
            self.running = False
            self.progress.stop()
            self.stop_btn.configure(state="disabled")

    def _show_results(self, hackers, analyses, tier_dist, stats):
        """Показать сводку результатов"""
        summary = f"""
📊 РЕЗУЛЬТАТЫ:
─────────────
• Хакеров в выборке: {len(hackers)}
• Средний Value Score: {stats.get('avg_value_score', 0):.2f}

🏆 Топ-5 хакеров:
"""
        top = sorted(analyses, key=lambda x: x.value_score, reverse=True)[:5]
        for i, h in enumerate(top, 1):
            summary += f"{i}. {h.username} | Tier: {h.tier.value} | Score: {h.value_score:.1f}\n"

        summary += f"\n📁 Файлы сохранены в: {self.settings['output_dir']}"

        self._log(summary, "success")

    def _stop_collection(self):
        """Остановить выполнение"""
        if self.running:
            self.running = False
            self.progress.stop()
            self._update_status("⏹ Остановлено пользователем", 'Error.TLabel')
            self._log("⚠ Сбор прерван", "warning")
            self.stop_btn.configure(state="disabled")

    def _clear_log(self):
        """Очистить лог"""
        self.log_text.configure(state='normal')
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state='disabled')
        self.log_messages = []
        self._update_status("Готов к запуску", 'Status.TLabel')


def main():
    """Точка входа GUI"""
    root = tk.Tk()
    app = HackerOneGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()