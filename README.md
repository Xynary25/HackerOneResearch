# 🔍 HackerOne Research Tool v3.0

**Инструмент для сбора и анализа данных о багхантерах платформы HackerOne**

---

## 📋 О проекте

HackerOne Research Tool — это комплексное решение для исследования экосистемы багбаунти-платформы HackerOne. Инструмент предназначен для сбора, обработки и анализа данных об активных участниках платформы с целью проектирования процессов привлечения хакеров на собственную багбаунти-платформу.

### 🎯 Назначение

- **Исследование рынка** — анализ активности и ценности багхантеров
- **Построение процессов рекрутинга** — выявление приоритетных кандидатов для привлечения
- **Бенчмаркинг** — сравнение метрик для настройки собственной платформы
- **Аналитика** — получение структурированных данных для принятия решений

### ⚠️ Важное уведомление

> Данный инструмент предназначен исключительно для образовательных и исследовательских целей. При использовании соблюдайте:
> - [Условия использования HackerOne](https://www.hackerone.com/terms)
> - Политику `robots.txt` целевого сайта
> - Принципы ответственного скрапинга (rate limiting, уважение к инфраструктуре)

---

## ✨ Возможности

### 📊 Сбор данных
- **7 категорий лидерборда**: репутация, High/Critical, OWASP Top 10, страны, типы активов, восходящие звёзды, голоса
- **Hacktivity** — сбор опубликованных отчётов об уязвимостях
- **Детальные профили** — опциональный углублённый сбор по конкретным хакерам
- **Rate limiting** — защита от блокировок с настраиваемыми задержками

### 🔧 Обработка
- **Нормализация** — приведение данных к стандартному диапазону
- **Обогащение** — расчёт производных метрик (value_score, activity_score, quality_score)
- **Классификация** — определение tier хакера (elite/premium/standard/novice)
- **Фильтрация** — отбор по критериям (tier, страна, минимальный score)

### 🧠 Анализ
- **Индивидуальный скоринг** — оценка ценности каждого хакера
- **Портфельная аналитика** — распределение по навыкам, географии, tier
- **Анализ отчётов** — severity, state, программы, баунти
- **Рекомендации** — генерация приоритетов для рекрутинга

### 📁 Экспорт
- **JSON** — для программной обработки и интеграций
- **CSV** — для быстрого просмотра и импорта
- **Excel (XLSX)** — для презентаций и отчётности с форматированием

### 🖥️ Интерфейсы
- **CLI** — интерактивный режим и аргументы командной строки
- **GUI** — графический интерфейс на Tkinter с таблицей результатов и логами

---

## 🚀 Быстрый старт

### Требования

- **Python**: 3.8 или выше
- **Google Chrome**: последняя стабильная версия
- **ОС**: Windows 10/11, Linux, macOS

### Установка

```bash
# 1. Клонируйте репозиторий
git clone <repository-url>
cd HackerOneResearch

# 2. Создайте виртуальное окружение
python -m venv venv

# 3. Активируйте окружение
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 4. Установите зависимости
pip install -r requirements.txt
```

### Проверка установки

```bash
python -m pip list | findstr "selenium beautifulsoup4 openpyxl"
```

---

## 📖 Использование

### 🖥️ Графический интерфейс (рекомендуется)

```bash
python gui.py
```

**Возможности GUI:**
- Выбор категории лидерборда из выпадающего списка
- Настройка лимитов хакеров и отчётов
- Выбор форматов экспорта (JSON/CSV/Excel)
- Таблица результатов с топ-20 хакерами
- Лог выполнения с цветовой индикацией
- Экспорт логов для диагностики
- Сохранение настроек между запусками

**Горячие клавиши:**
- `F5` — Запустить сбор
- `Escape` — Остановить сбор
- `Ctrl+Q` — Выход из приложения

---

### 💻 Командная строка (CLI)

#### Интерактивный режим

```bash
python main.py
```

#### Быстрый запуск с параметрами

```bash
# Базовый запуск
python main.py --limit 50 --reports 50

# С выбором категории и экспортом
python main.py --category owasp --limit 30 --export json csv

# С окном браузера (для отладки)
python main.py --headless false --debug

# Полная команда
python main.py --category reputation --limit 40 --reports 40 --headless true --export json csv excel --debug
```

#### Доступные аргументы

| Аргумент | Описание | Значение по умолчанию |
|----------|----------|----------------------|
| `--limit` | Количество хакеров (5-100) | 20 |
| `--reports` | Количество отчётов (10-100) | 30 |
| `--headless` | Режим браузера (true/false) | true |
| `--category` | Категория лидерборда | reputation |
| `--export` | Форматы экспорта | json csv |
| `--interactive` | Интерактивный режим ввода | false |
| `--debug` | Режим отладки (подробные логи) | false |

#### Категории лидерборда

| Категория | Ключ | Описание |
|-----------|------|----------|
| 🏆 По репутации | `reputation` | Общий рейтинг хакеров |
| 🔴 High/Critical | `high_critical` | По серьёзным уязвимостям |
| 🛡️ OWASP Top 10 | `owasp` | По уязвимостям OWASP |
| 🌍 По странам | `country` | Географический рейтинг |
| 💻 По типу активов | `asset_type` | Web, Mobile, API |
| 📈 Восходящие звёзды | `up_and_comers` | Новые активные хакеры |
| 👍 По голосам | `upvotes` | По оценкам сообщества |

---

## 📁 Структура проекта

```
HackerOneResearch/
├── main.py                      # 🎯 Точка входа CLI
├── gui.py                       # 🖥️ Графический интерфейс
├── config.yaml                  # ⚙️ Конфигурация
├── requirements.txt             # 📦 Зависимости
├── README.md                    # 📖 Документация
│
├── src/
│   ├── __init__.py
│   │
│   ├── clients/
│   │   ├── __init__.py
│   │   └── hackerone_scraper.py    # 🕷️ Selenium-скрапер
│   │
│   ├── collectors/
│   │   ├── __init__.py
│   │   └── data_collectors.py      # 📥 Сбор данных
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   └── data_processors.py      # 🔧 Нормализация
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   └── data_analyzers.py       # 🧠 Скоринг и анализ
│   │
│   ├── exporters/
│   │   ├── __init__.py
│   │   └── data_exporters.py       # 💾 Экспорт JSON/CSV/Excel
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── entities.py             # 📊 Модели данных
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # ⚙️ Настройки приложения
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py              # 🔧 Вспомогательные функции
│
├── data/
│   ├── debug/              # 🐛 HTML для отладки
│   └── processed/          # ✅ Результаты экспорта
│
└── logs/                   # 📋 Логи выполнения
```

---

## ⚙️ Конфигурация

### Файл `config.yaml`

```yaml
hackerone:
  api:
    rate_limit:
      requests_per_minute: 30
      delay_between_requests: 2.0
      max_retries: 3
      timeout: 30
  scraper:
    base_url: "https://hackerone.com"
    leaderboard_url: "https://hackerone.com/leaderboard"
    hacktivity_url: "https://hackerone.com/hacktivity"
    scroll_iterations: 5
    wait_timeout: 30
    default_category: "reputation"

analysis:
  metrics_weights:
    reputation: 0.40
    signal: 0.30
    impact: 0.30
  tier_thresholds:
    elite: 70
    premium: 55
    standard: 40

export:
  formats:
    - json
    - csv
    - excel
  output_dir: "processed"
  include_timestamp: true
  export_excel: true
```

### Настройки GUI

Настройки графического интерфейса автоматически сохраняются в файл `gui_settings.json` в папке с приложением и загружаются при следующем запуске.

---

## 📊 Модели данных

### HackerProfile
| Поле | Тип | Описание |
|------|-----|----------|
| `username` | str | Уникальное имя хакера |
| `reputation` | int | Репутация на платформе |
| `signal` | float | Метрика качества (0-100) |
| `impact` | int | Суммарная серьёзность уязвимостей |
| `total_bounties` | float | Общая сумма выплат |
| `total_reports` | int | Количество отчётов |
| `accepted_reports` | int | Принятые отчёты |
| `acceptance_rate` | float | Процент принятия |
| `rank` | int | Позиция в лидерборде |
| `country` | str | Страна |
| `skills` | List[str] | Навыки |
| `is_verified` | bool | Статус верификации |
| `value_score` | float | Комплексная оценка (0-100) |
| `activity_score` | float | Оценка активности (0-100) |
| `quality_score` | float | Оценка качества (0-100) |
| `tier` | Enum | Категория (elite/premium/standard/novice) |

### BugReport
| Поле | Тип | Описание |
|------|-----|----------|
| `report_id` | int | ID отчёта |
| `title` | str | Заголовок |
| `state` | Enum | Состояние (new/triaged/resolved/closed) |
| `hacker_username` | str | Автор отчёта |
| `program_name` | str | Программа |
| `bounty_amount` | float | Выплата |
| `severity` | str | Критичность |
| `disclosed_at` | datetime | Дата публикации |

### HackerValueAnalysis
| Поле | Тип | Описание |
|------|-----|----------|
| `username` | str | Имя хакера |
| `value_score` | float | Общая ценность |
| `activity_score` | float | Активность |
| `quality_score` | float | Качество |
| `tier` | Enum | Категория |
| `strengths` | List[str] | Сильные стороны |
| `weaknesses` | List[str] | Слабые стороны |
| `recommendations` | List[str] | Рекомендации |
| `recruitment_priority` | str | Приоритет (high/medium/low) |

---

## 🧮 Формулы расчёта метрик

### Value Score (0-100)
```python
value_score = (
    0.40 × min(reputation / 10000, 1.0) +
    0.30 × min(signal / 100, 1.0) +
    0.30 × min(impact / 50000, 1.0)
) × 100
```

**Обоснование весов:**
- **40% репутация** — интегральный показатель долгосрочного вклада
- **30% signal** — актуальная метрика качества отчётов
- **30% impact** — серьёзность найденных уязвимостей

### Activity Score (0-100)
```python
activity_score = min(100, (
    min(total_reports / 100, 1.0) × 40 +
    acceptance_rate × 40 +
    (20 if is_verified else 0)
))
```

**Компоненты:**
- **40 баллов** — количество отчётов (максимум при 100+)
- **40 баллов** — процент принятия отчётов
- **20 баллов** — бонус за верификацию

### Quality Score (0-100)
```python
quality_score = min(100, (
    acceptance_rate × 50 +
    min(avg_bounty / 1000, 1.0) × 30 +
    min(impact / 50000, 1.0) × 20
))
```

**Компоненты:**
- **50 баллов** — процент принятия отчётов
- **30 баллов** — средний размер баунти
- **20 баллов** — общий impact

### Tier Thresholds
| Score | Tier | Описание |
|-------|------|----------|
| ≥ 70 | **elite** | Топ-уровень, приоритет #1 |
| ≥ 55 | **premium** | Высокий уровень |
| ≥ 40 | **standard** | Средний уровень |
| < 40 | **novice** | Начинающий |

### Recruitment Priority
| Условия | Priority |
|---------|----------|
| elite/premium + activity > 40 | **high** |
| premium/standard | **medium** |
| остальные | **low** |

---

## 🔧 Расширение функционала

### Добавление новой категории лидерборда

1. Откройте `src/clients/hackerone_scraper.py`
2. Добавьте категорию в словарь `CATEGORIES`:
```python
CATEGORIES = {
    # ... существующие категории
    "new_category": "/leaderboard/new_category"
}
```
3. Обновите `CATEGORIES_DISPLAY` в `main.py` или `gui.py`

### Добавление новой метрики

1. Откройте `src/models/entities.py`
2. Добавьте поле в класс `HackerProfile`:
```python
new_metric: float = 0.0
```
3. Реализуйте расчёт в `src/processors/data_processors.py`
4. Обновите `to_dict()` метод для экспорта

### Интеграция с базой данных

Для продакшена рекомендуется добавить сохранение в PostgreSQL:

```python
# Пример расширения Exporters
class DatabaseExporter:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
    
    def export(self, hackers: List[Dict], table_name: str):
        df = pd.DataFrame(hackers)
        df.to_sql(table_name, self.engine, if_exists='append', index=False)
```

---

## 🐛 Troubleshooting

### Ошибка: "ChromeDriver не найден"

**Решение:**
```bash
# Автоматическая установка через webdriver-manager
pip install --upgrade webdriver-manager

# Или вручную скачайте с https://chromedriver.chromium.org/
```

### Ошибка: "Собрано 0 профилей"

**Возможные причины:**
1. Проблемы с подключением к интернету
2. Блокировка со стороны HackerOne (слишком частые запросы)
3. Изменения в структуре сайта

**Решения:**
- Увеличьте `delay_between_requests` в `config.yaml`
- Проверьте файлы в `data/debug/` для диагностики
- Запустите с `--headless false` для визуальной отладки

### Ошибка: "Excel экспорт недоступен"

**Решение:**
```bash
pip install openpyxl
```

### Ошибка: "ModuleNotFoundError: No module named 'src'"

**Решение:**
```bash
# Убедитесь, что запускаете из корня проекта
cd HackerOneResearch
python main.py

# Или установите пакет в режиме разработки
pip install -e .
```

### Ошибка: "Слишком много запросов"

**Решение:**
1. Увеличьте задержку в `config.yaml`:
```yaml
delay_between_requests: 5.0
```
2. Уменьшите `requests_per_minute`:
```yaml
requests_per_minute: 15
```
3. Добавьте прокси (для продакшена)

---

## 📈 Примеры использования данных

### Для рекрутинга

```python
# Фильтрация приоритетных кандидатов
from src.processors.data_processors import DataFilter

filter = DataFilter(config)
priority_hackers = filter.filter_by_tier(hackers, HackerTier.PREMIUM)
priority_hackers = filter.filter_by_min_score(priority_hackers, 55)
```

### Для бенчмаркинга программ

```python
# Анализ распределения баунти
from src.analyzers.data_analyzers import ReportAnalyzer

avg_bounty = ReportAnalyzer.calculate_avg_bounty(reports)
total_bounty = ReportAnalyzer.calculate_total_bounties(reports)
```

### Для географического таргетирования

```python
# Анализ по странам
from src.analyzers.data_analyzers import PortfolioAnalyzer

geo_stats = PortfolioAnalyzer.analyze_geography(hackers)
for country, stats in geo_stats.items():
    print(f"{country}: {stats['count']} хакеров, средний score: {stats['avg_value_score']}")
```

---

## 🛡️ Безопасность и этика

### Принципы ответственного скрапинга

1. **Rate Limiting** — соблюдаете задержки между запросами (по умолчанию 2-4 сек)
2. **User-Agent** — используете реалистичную строку браузера
3. **Объём данных** — не собираете данные в промышленных масштабах без согласования
4. **Личные данные** — не собираете конфиденциальную информацию
5. **Нагрузка** — не создаёте чрезмерную нагрузку на инфраструктуру

### Рекомендации для продакшена

- Используйте официальное API HackerOne (если доступно)
- Получите письменное разрешение перед масштабным сбором
- Рассмотрите альтернативные источники данных
- Реализуйте кэширование для снижения количества запросов
- Добавьте поддержку прокси-ротации

---

## 📝 Лицензия

MIT License — свободное использование с указанием авторства.

```
Copyright (c) 2026 Xynary25

Данное программное обеспечение предоставляется "как есть", без каких-либо гарантий.
```

---

## 👨‍💻 Автор

**Xynary25**  
2026
---

## 📞 Контакты

- [GitHub](https://github.com/Xynary25)
- [Email](xynary56@gmail.com)

---

## 🙏 Благодарности

- [HackerOne](https://hackerone.com) — платформа для исследований
- [Selenium](https://selenium.dev) — автоматизация браузера
- [BeautifulSoup](https://beautiful-soup-4.readthedocs.io) — парсинг HTML
- [OpenPyXL](https://openpyxl.readthedocs.io) — работа с Excel

---

## 📚 Дополнительные ресурсы

- [Документация Python](https://docs.python.org/3/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [HackerOne API](https://api.hackerone.com/)
- [Bug Bounty Forum](https://www.bugbountyforum.com/)

---

**⭐ Если проект был полезен — поставьте звезду на GitHub!**ц
