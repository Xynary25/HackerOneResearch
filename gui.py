#!/usr/bin/env python3
"""
HackerOne Research Tool v3.0
Расширенный GUI с категориями, настройками и улучшенным интерфейсом
ИСПРАВЛЕНО: Сохранение/загрузка настроек, Ctrl+Q, подтверждение выхода
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

# === КОНФИГУРАЦИЯ ИНТЕРФЕЙСА ===
APP_VERSION = "3.0.0"
APP_AUTHOR = "Xynary25"
APP_NAME = "HackerOne Research Tool"

# ✅ Путь к файлу настроек
SETTINGS_FILE = Path(__file__).parent / "gui_settings.json"

CATEGORIES = {
    "reputation": "🏆 По репутации",
    "high_critical": "🔴 High/Critical уязвимости",
    "owasp": "🛡️ OWASP Top 10",
    "country": "🌍 По странам",
    "asset_type": "💻 По типу активов",
    "up_and_comers": "📈 Восходящие звёзды",
    "upvotes": "👍 По голосам"
}

# ✅ Настройки по умолчанию
DEFAULT_SETTINGS = {
    "limit": 20,
    "reports": 30,
    "headless": True,
    "category": "reputation",
    "export_json": True,
    "export_csv": True,
    "export_excel": False,
    "output_dir": "data/processed"
}


class HackerOneGUI:
    """Основной класс GUI приложения"""

    def __init__(self, root):
        self.root = root
        self.root.title(f"🔍 {APP_NAME} v{APP_VERSION}")
        self.root.geometry("1000x750")
        self.root.minsize(800, 600)
        self.root.configure(bg='#f0f0f0')

        # ✅ Инициализация настроек
        self.settings = DEFAULT_SETTINGS.copy()

        self.config = None
        self.running = False
        self.log_messages = []

        # Создаём директорию для логов
        self.logs_dir = Path(__file__).parent / 'logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # ✅ Загрузка настроек из файла при старте
        self._load_settings()

        self._setup_styles()
        self._create_menu()
        self._create_widgets()
        # ✅ Настройка горячих клавиш (после создания виджетов)
        self._setup_bindings()

    # ========================================================================
    # ✅ МЕТОДЫ ДЛЯ РАБОТЫ С НАСТРОЙКАМИ
    # ========================================================================

    def _load_settings(self):
        """
        ✅ Загрузка настроек из файла при старте приложения

        Если файл gui_settings.json существует, настройки загружаются из него.
        Если файл не найден или повреждён, используются настройки по умолчанию.
        """
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)

                # Обновляем текущие настройки сохранёнными значениями
                self.settings.update(saved_settings)

                # Валидация загруженных настроек
                self.settings['limit'] = max(5, min(100, self.settings.get('limit', 20)))
                self.settings['reports'] = max(10, min(100, self.settings.get('reports', 30)))

                print(f"✅ Настройки загружены из {SETTINGS_FILE}")
                print(f"   Категория: {self.settings.get('category', 'reputation')}")
                print(f"   Лимит хакеров: {self.settings.get('limit', 20)}")
                print(f"   Лимит отчётов: {self.settings.get('reports', 30)}")
                print(f"   Headless: {self.settings.get('headless', True)}")

            except json.JSONDecodeError as e:
                print(f"⚠ Ошибка парсинга файла настроек: {e}")
                print("   Используются настройки по умолчанию")
                self.settings = DEFAULT_SETTINGS.copy()
            except Exception as e:
                print(f"⚠ Ошибка загрузки настроек: {e}")
                print("   Используются настройки по умолчанию")
                self.settings = DEFAULT_SETTINGS.copy()
        else:
            print(f"ℹ Файл настроек не найден: {SETTINGS_FILE}")
            print("   Используются настройки по умолчанию")
            self.settings = DEFAULT_SETTINGS.copy()

    def _save_settings(self):
        """
        ✅ Сохранение текущих настроек в файл

        Автоматически вызывается:
        - При запуске сбора данных
        - При закрытии приложения
        - При ручном сохранении через меню
        """
        try:
            # Создаём директорию если не существует
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)

            print(f"✅ Настройки сохранены в {SETTINGS_FILE}")
            return True

        except PermissionError as e:
            print(f"❌ Ошибка доступа при сохранении настроек: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка сохранения настроек: {e}")
            return False

    def _save_settings_to_file(self):
        """
        ✅ Ручное сохранение настроек через меню
        """
        if self._save_settings():
            self._log("💾 Настройки сохранены в файл", "success")
            messagebox.showinfo(
                "Настройки",
                f"Настройки успешно сохранены в:\n{SETTINGS_FILE}"
            )
        else:
            self._log("❌ Ошибка сохранения настроек", "error")
            messagebox.showerror(
                "Ошибка",
                "Не удалось сохранить настройки.\nПроверьте права доступа к папке."
            )

    def _reset_settings(self):
        """
        ✅ Сброс настроек к значениям по умолчанию
        """
        self.settings = DEFAULT_SETTINGS.copy()

        # Обновляем значения в виджетах
        self.limit_var.set(20)
        self.reports_var.set(30)
        self.headless_var.set(True)
        self.category_var.set("🏆 По репутации")
        self.export_json_var.set(True)
        self.export_csv_var.set(True)
        self.export_excel_var.set(False)
        self.output_var.set("data/processed")

        self._log("⚙️ Настройки сброшены к значениям по умолчанию", "warning")
        messagebox.showinfo(
            "Настройки",
            "Настройки сброшены к значениям по умолчанию"
        )

    # ========================================================================
    # ✅ МЕТОДЫ НАСТРОЙКИ ИНТЕРФЕЙСА
    # ========================================================================

    def _setup_styles(self):
        """Настройка современных стилей интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')

        # Цветовая схема
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=8)
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#2c3e50')
        style.configure('Subheader.TLabel', font=('Segoe UI', 11, 'bold'), foreground='#34495e')
        style.configure('Status.TLabel', foreground='#2980b9', font=('Segoe UI', 10))
        style.configure('Success.TLabel', foreground='#27ae60', font=('Segoe UI', 10, 'bold'))
        style.configure('Error.TLabel', foreground='#e74c3c', font=('Segoe UI', 10, 'bold'))
        style.configure('Warning.TLabel', foreground='#f39c12', font=('Segoe UI', 10))

        # Стили для прогресс-бара
        style.configure('Horizontal.TProgressbar',
                        background='#3498db',
                        troughcolor='#ecf0f1',
                        thickness=20)

        # Стили для Treeview (таблица результатов)
        style.configure('Treeview',
                        background='#ffffff',
                        foreground='#2c3e50',
                        fieldbackground='#ffffff',
                        font=('Segoe UI', 9),
                        rowheight=25)
        style.configure('Treeview.Heading',
                        font=('Segoe UI', 10, 'bold'),
                        background='#34495e',
                        foreground='#ffffff')

    def _create_menu(self):
        """Создание главного меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 Файл", menu=file_menu)
        file_menu.add_command(label="📂 Открыть папку результатов", command=self._open_output_folder)
        file_menu.add_command(label="📥 Экспорт логов", command=self._export_logs)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Выход", command=self._on_closing)

        # Меню Настройки
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="⚙️ Настройки", menu=settings_menu)
        settings_menu.add_command(label="🔄 Сбросить настройки", command=self._reset_settings)
        settings_menu.add_command(label="💾 Сохранить настройки", command=self._save_settings_to_file)

        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Справка", menu=help_menu)
        help_menu.add_command(label="ℹ️ О приложении", command=self._show_about)
        help_menu.add_command(label="📖 Документация", command=self._show_help)
        help_menu.add_command(label="🔑 Формулы расчёта", command=self._show_formulas)

    def _create_widgets(self):
        """Создание виджетов интерфейса"""
        # === Главный контейнер ===
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # === Заголовок ===
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=4, pady=(0, 15), sticky="ew")

        title_label = ttk.Label(header_frame,
                                text=f"🔍 {APP_NAME}",
                                style='Header.TLabel')
        title_label.pack(side="left")

        version_label = ttk.Label(header_frame,
                                  text=f"v{APP_VERSION}",
                                  style='Subheader.TLabel',
                                  foreground='#7f8c8d')
        version_label.pack(side="right", padx=10)

        # === Настройки сбора (левая колонка) ===
        settings_frame = ttk.LabelFrame(main_frame, text="📊 Настройки сбора", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(0, 5), pady=5)

        # Категория лидерборда
        ttk.Label(settings_frame, text="Категория:", style='Subheader.TLabel').grid(
            row=0, column=0, sticky="w", pady=5)
        self.category_var = tk.StringVar(value=CATEGORIES.get(self.settings["category"], "🏆 По репутации"))
        category_combo = ttk.Combobox(settings_frame,
                                      textvariable=self.category_var,
                                      values=list(CATEGORIES.values()),
                                      state="readonly",
                                      width=35)
        category_combo.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        category_combo.bind('<<ComboboxSelected>>', self._on_category_change)

        # Лимит хакеров
        ttk.Label(settings_frame, text="Лимит хакеров:").grid(row=1, column=0, sticky="w", pady=5)
        self.limit_var = tk.IntVar(value=self.settings["limit"])
        limit_spin = ttk.Spinbox(settings_frame, from_=5, to=100,
                                 textvariable=self.limit_var, width=10)
        limit_spin.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # Лимит отчётов
        ttk.Label(settings_frame, text="Лимит отчётов:").grid(row=2, column=0, sticky="w", pady=5)
        self.reports_var = tk.IntVar(value=self.settings["reports"])
        reports_spin = ttk.Spinbox(settings_frame, from_=10, to=100,
                                   textvariable=self.reports_var, width=10)
        reports_spin.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        # Headless режим
        self.headless_var = tk.BooleanVar(value=self.settings["headless"])
        headless_check = ttk.Checkbutton(settings_frame,
                                         text="Запуск в фоне (headless)",
                                         variable=self.headless_var)
        headless_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)

        # === Настройки экспорта (правая колонка) ===
        export_frame = ttk.LabelFrame(main_frame, text="📁 Настройки экспорта", padding="10")
        export_frame.grid(row=1, column=2, columnspan=2, sticky="nsew", padx=(5, 0), pady=5)

        self.export_json_var = tk.BooleanVar(value=self.settings["export_json"])
        self.export_csv_var = tk.BooleanVar(value=self.settings["export_csv"])
        self.export_excel_var = tk.BooleanVar(value=self.settings["export_excel"])

        json_check = ttk.Checkbutton(export_frame, text="JSON", variable=self.export_json_var)
        json_check.grid(row=0, column=0, sticky="w", pady=3)

        csv_check = ttk.Checkbutton(export_frame, text="CSV", variable=self.export_csv_var)
        csv_check.grid(row=0, column=1, sticky="w", pady=3)

        excel_check = ttk.Checkbutton(export_frame, text="Excel (XLSX)", variable=self.export_excel_var)
        excel_check.grid(row=0, column=2, sticky="w", pady=3)

        # Папка вывода
        ttk.Label(export_frame, text="Папка вывода:").grid(row=1, column=0, sticky="w", pady=(15, 5))
        self.output_var = tk.StringVar(value=self.settings["output_dir"])
        output_entry = ttk.Entry(export_frame, textvariable=self.output_var, width=30)
        output_entry.grid(row=2, column=0, columnspan=3, sticky="we", pady=5)
        browse_btn = ttk.Button(export_frame, text="Обзор...", command=self._browse_folder)
        browse_btn.grid(row=2, column=3, sticky="e", padx=5)

        # === Статус и прогресс ===
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=10)

        ttk.Label(status_frame, text="Статус:", style='Subheader.TLabel').pack(side="left")
        self.status_var = tk.StringVar(value="Готов к запуску")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      style='Status.TLabel', wraplength=700)
        self.status_label.pack(side="left", padx=10)

        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=400)
        self.progress.pack(side="right", padx=10)

        # === Кнопки управления ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=10)

        run_btn = ttk.Button(btn_frame, text="▶ Запустить сбор",
                             command=self._start_collection,
                             style='TButton')
        run_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="⏹ Остановить",
                                   command=self._stop_collection,
                                   state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        clear_btn = ttk.Button(btn_frame, text="🗑 Очистить лог",
                               command=self._clear_log)
        clear_btn.pack(side="left", padx=5)

        export_log_btn = ttk.Button(btn_frame, text="📥 Экспорт логов",
                                    command=self._export_logs)
        export_log_btn.pack(side="left", padx=5)

        # === Таблица результатов ===
        results_frame = ttk.LabelFrame(main_frame, text="📊 Результаты", padding="10")
        results_frame.grid(row=4, column=0, columnspan=4, sticky="nsew", pady=5)
        main_frame.rowconfigure(4, weight=1)

        # Создаём Treeview для таблицы
        columns = ("username", "tier", "value", "reputation", "signal", "impact", "priority")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=10)

        # Настройка колонок
        self.results_tree.heading("username", text="Username")
        self.results_tree.heading("tier", text="Tier")
        self.results_tree.heading("value", text="Value Score")
        self.results_tree.heading("reputation", text="Reputation")
        self.results_tree.heading("signal", text="Signal")
        self.results_tree.heading("impact", text="Impact")
        self.results_tree.heading("priority", text="Priority")

        self.results_tree.column("username", width=150)
        self.results_tree.column("tier", width=80)
        self.results_tree.column("value", width=80)
        self.results_tree.column("reputation", width=90)
        self.results_tree.column("signal", width=80)
        self.results_tree.column("impact", width=90)
        self.results_tree.column("priority", width=80)

        # Скроллбары
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.results_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # === Лог вывода ===
        log_frame = ttk.LabelFrame(main_frame, text="📋 Лог выполнения", padding="10")
        log_frame.grid(row=5, column=0, columnspan=4, sticky="nsew", pady=5)
        main_frame.rowconfigure(5, weight=1)

        self.log_text = tk.Text(log_frame, height=8, width=80,
                                font=('Consolas', 9),
                                state='disabled',
                                bg='#ffffff',
                                fg='#2c3e50')
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Настройка тегов для цветов в логе
        self.log_text.tag_configure("info", foreground="#2c3e50")
        self.log_text.tag_configure("success", foreground="#27ae60")
        self.log_text.tag_configure("error", foreground="#e74c3c")
        self.log_text.tag_configure("warning", foreground="#f39c12")

        # === Нижняя панель ===
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=6, column=0, columnspan=4, pady=(15, 0))

        ttk.Label(footer_frame,
                  text=f"© 2026 {APP_AUTHOR} | {APP_NAME} v{APP_VERSION}",
                  foreground='#7f8c8d').pack(side="left")

        self.stats_label = ttk.Label(footer_frame, text="", foreground='#3498db')
        self.stats_label.pack(side="right")

    def _setup_bindings(self):
        """
        ✅ Настройка горячих клавиш

        Поддерживаемые комбинации:
        - Ctrl+Q / Ctrl+q — Выход из приложения
        - F5 — Запустить сбор данных
        - Escape — Остановить сбор данных
        """
        # ✅ Выход (оба регистра)
        self.root.bind('<Control-q>', lambda e: self._on_closing())
        self.root.bind('<Control-Q>', lambda e: self._on_closing())

        # Запуск сбора
        self.root.bind('<F5>', lambda e: self._start_collection() if not self.running else None)

        # Остановка сбора
        self.root.bind('<Escape>', lambda e: self._stop_collection() if self.running else None)

    # ========================================================================
    # ✅ МЕТОДЫ ОБРАБОТКИ СОБЫТИЙ
    # ========================================================================

    def _on_category_change(self, event):
        """Обработка смены категории"""
        selected = self.category_var.get()
        for key, value in CATEGORIES.items():
            if value == selected:
                self.settings["category"] = key
                self._log(f"📊 Категория изменена: {value}", "info")
                break

    def _browse_folder(self):
        """Открыть диалог выбора папки"""
        folder = filedialog.askdirectory(initialdir="data/processed")
        if folder:
            self.output_var.set(folder)
            self._log(f"📂 Папка вывода: {folder}", "info")

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
        self.log_text.insert("end", f"{log_entry}\n", level)
        self.log_text.see("end")
        self.log_text.configure(state='disabled')

    def _export_logs(self):
        """Экспорт логов в файл"""
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
                        "app_version": APP_VERSION,
                        "total_messages": len(self.log_messages),
                        "logs": self.log_messages
                    }, f, indent=2, ensure_ascii=False)

                self._log(f"✓ Лог экспортирован: {filepath}", "success")
                messagebox.showinfo("Успех", f"Лог сохранён:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить лог:\n{str(e)}")
                self._log(f"❌ Ошибка экспорта лога: {e}", "error")

    def _open_output_folder(self):
        """Открыть папку с результатами"""
        output_path = Path(self.output_var.get())
        if output_path.exists():
            os.startfile(output_path)
        else:
            messagebox.showwarning("Предупреждение", "Папка результатов не найдена")

    def _update_status(self, message, style='Status.TLabel'):
        """Обновить статус"""
        self.status_var.set(message)
        self.status_label.configure(style=style)

    # ========================================================================
    # ✅ МЕТОДЫ СБОРА ДАННЫХ
    # ========================================================================

    def _start_collection(self):
        """Запустить сбор данных в отдельном потоке"""
        if self.running:
            return

        if not any([self.export_json_var.get(), self.export_csv_var.get(), self.export_excel_var.get()]):
            messagebox.showwarning("Предупреждение", "Выберите хотя бы один формат экспорта!")
            return

        # Обновление настроек из виджетов
        self.settings.update({
            "limit": self.limit_var.get(),
            "reports": self.reports_var.get(),
            "headless": self.headless_var.get(),
            "category": self.settings.get("category", "reputation"),
            "export_json": self.export_json_var.get(),
            "export_csv": self.export_csv_var.get(),
            "export_excel": self.export_excel_var.get(),
            "output_dir": self.output_var.get()
        })

        # ✅ Автосохранение настроек при запуске
        self._save_settings()

        # Блокировка интерфейса
        self.running = True
        self.progress.start(10)
        self._update_status("Инициализация...", 'Status.TLabel')
        self.stop_btn.configure(state="normal")

        self._log(
            f"Запуск: category={self.settings['category']}, limit={self.settings['limit']}, reports={self.settings['reports']}",
            "info")

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
            self._update_status(f"Сбор лидерборда ({CATEGORIES.get(self.settings['category'], 'reputation')})...",
                                'Status.TLabel')
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

            if self.export_excel_var.get():
                excel_exporter = ExcelExporter(output_dir)
                if hackers_data:
                    exported_files.append(excel_exporter.export(hackers_data, f"hackers_{timestamp}"))
                if analyses_data:
                    exported_files.append(excel_exporter.export(analyses_data, f"analyses_{timestamp}"))

            self._log(f"✓ Экспортировано {len(exported_files)} файлов", "success")
            for f in exported_files:
                self._log(f"  📁 {f}", "info")

            # 7. Показ результатов в таблице
            self._show_results_in_table(hackers, analyses)

            # 8. Обновление статистики
            self._update_stats(stats, tier_dist)

            # 9. Завершение
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

    def _show_results_in_table(self, hackers, analyses):
        """Показать результаты в таблице"""
        # Очистка таблицы
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Добавление данных (топ-20)
        combined = list(zip(hackers[:20], analyses[:20]))
        for hacker, analysis in combined:
            self.results_tree.insert("", "end", values=(
                analysis.username,
                analysis.tier.value.upper(),
                f"{analysis.value_score:.1f}",
                hacker.reputation,
                f"{hacker.signal:.1f}",
                hacker.impact,
                analysis.recruitment_priority.upper()
            ))

        self._log(f"📊 Показано {len(combined)} результатов в таблице", "success")

    def _update_stats(self, stats, tier_dist):
        """Обновить статистику в нижней панели"""
        stats_text = (
            f"Всего: {stats.get('total_hackers', 0)} | "
            f"Elite: {tier_dist.get('elite', 0)} | "
            f"Premium: {tier_dist.get('premium', 0)} | "
            f"Standard: {tier_dist.get('standard', 0)} | "
            f"Средний score: {stats.get('avg_value_score', 0):.1f}"
        )
        self.stats_label.configure(text=stats_text)

    def _stop_collection(self):
        """Остановить выполнение"""
        if self.running:
            self.running = False
            self.progress.stop()
            self._update_status("⏹ Остановлено пользователем", 'Warning.TLabel')
            self._log("⚠ Сбор прерван", "warning")
            self.stop_btn.configure(state="disabled")

    def _clear_log(self):
        """Очистить лог"""
        self.log_text.configure(state='normal')
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state='disabled')
        self.log_messages = []
        self._update_status("Готов к запуску", 'Status.TLabel')
        self.stats_label.configure(text="")

    # ========================================================================
    # ✅ МЕТОДЫ СПРАВОЧНОЙ ИНФОРМАЦИИ
    # ========================================================================

    def _show_about(self):
        """Показать информацию о приложении"""
        about_text = f"""
{APP_NAME} v{APP_VERSION}

Автор: {APP_AUTHOR}
Год: 2026

Описание:
Инструмент для сбора и анализа данных о багхантерах 
платформы HackerOne. Предназначен для исследования 
и построения процессов привлечения хакеров.

Функции:
• Сбор данных из лидерборда (7 категорий)
• Сбор данных из Hacktivity
• Расчёт метрик (Value, Activity, Quality Score)
• Определение tier хакеров (Elite/Premium/Standard/Novice)
• Экспорт в JSON, CSV, Excel
• Детальное логирование

Технологии:
• Python 3.8+
• Selenium WebDriver
• BeautifulSoup4
• OpenPyXL (Excel)
• Tkinter (GUI)

© 2026 Все права защищены
        """
        messagebox.showinfo(f"О приложении {APP_NAME}", about_text)

    def _show_help(self):
        """Показать справку"""
        help_text = """
📖 КРАТКАЯ СПРАВКА

Запуск сбора:
• Нажмите "▶ Запустить сбор" или F5
• Выберите категорию лидерборда
• Настройте лимиты хакеров и отчётов
• Выберите форматы экспорта

Категории лидерборда:
• 🏆 По репутации — общий рейтинг
• 🔴 High/Critical — по серьёзным уязвимостям
• 🛡️ OWASP Top 10 — по уязвимостям OWASP
• 🌍 По странам — географический рейтинг
• 💻 По типу активов — web, mobile, API
• 📈 Восходящие звёзды — новые хакеры
• 👍 По голосам — по сообществу

Горячие клавиши:
• F5 — Запустить сбор
• Escape — Остановить
• Ctrl+Q — Выход

Результаты:
• Таблица с топ-20 хакеров
• Лог выполнения
• Экспортированные файлы в папке вывода
        """
        messagebox.showinfo("Справка", help_text)

    def _show_formulas(self):
        """Показать формулы расчёта"""
        formulas_text = """
🔑 ФОРМУЛЫ РАСЧЁТА

Value Score (0-100):
  = (0.40 × rep_norm + 0.30 × signal_norm + 0.30 × impact_norm) × 100

  где:
  • rep_norm = min(reputation / 10000, 1.0)
  • signal_norm = min(signal / 100, 1.0)
  • impact_norm = min(impact / 50000, 1.0)

Activity Score (0-100):
  = min(reports/100, 1.0) × 40 + acceptance_rate × 40 + verified_bonus

Quality Score (0-100):
  = acceptance_rate × 50 + min(avg_bounty/1000, 1.0) × 30 + min(impact/50000, 1.0) × 20

Tier Thresholds:
  • Elite    ≥ 70
  • Premium  ≥ 55
  • Standard ≥ 40
  • Novice   < 40

Recruitment Priority:
  • High   — Elite/Premium + Activity > 40
  • Medium — Premium/Standard
  • Low    — Остальные
        """
        messagebox.showinfo("Формулы расчёта", formulas_text)

    # ========================================================================
    # ✅ МЕТОДЫ ЗАВЕРШЕНИЯ РАБОТЫ
    # ========================================================================

    def _on_closing(self):
        """
        ✅ Обработчик закрытия окна с подтверждением

        Проверяет:
        - Выполняется ли сбор данных
        - Подтверждает ли пользователь выход

        Сохраняет настройки перед закрытием.
        """
        if self.running:
            # Если сбор данных выполняется
            result = messagebox.askyesno(
                "⚠ Предупреждение",
                "Выполняется сбор данных.\n\n"
                "Остановить и выйти?\n\n"
                "⚠ Незавершённый сбор будет потерян.",
                icon='warning'
            )
            if result:
                self._stop_collection()
                self._save_settings()  # ✅ Сохранение настроек
                self._log("🚪 Приложение закрыто", "info")
                self.root.destroy()
        else:
            # Если сбор данных не выполняется
            result = messagebox.askyesno(
                "✅ Выход",
                "Вы уверены, что хотите выйти?\n\n"
                f"Настройки будут сохранены в:\n{SETTINGS_FILE}",
                icon='question'
            )
            if result:
                self._save_settings()  # ✅ Сохранение настроек
                self._log("🚪 Приложение закрыто", "info")
                self.root.destroy()


def main():
    """Точка входа GUI"""
    root = tk.Tk()

    # Установка иконки (если есть)
    icon_path = Path(__file__).parent / "icon.ico"
    if icon_path.exists():
        root.iconbitmap(str(icon_path))

    app = HackerOneGUI(root)
    root.protocol("WM_DELETE_WINDOW", app._on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()