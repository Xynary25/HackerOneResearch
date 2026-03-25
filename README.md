# HackerOne Research Tool

Инструмент для сбора и анализа данных о багхантерах платформы HackerOne. Предназначен для исследования активных и ценных участников с целью проектирования процессов привлечения на платформу Standoff.

## Возможности

- Сбор данных из лидерборда HackerOne (username, reputation, signal, impact)
- Сбор данных из Hacktivity (отчёты об уязвимостях)
- Нормализация и обогащение данных вычисляемыми метриками
- Расчёт value_score, activity_score, quality_score
- Определение tier хакера (novice, standard, premium, elite)
- Экспорт результатов в JSON и CSV форматы
- Контекстные менеджеры для работы с ресурсами
- Обработка ошибок и отсутствие Chrome
- Логирование в файл и консоль

## Установка

```bash
pip install -r requirements.txt
```

### Зависимости

- Python 3.8+
- Google Chrome (для скрапинга)
- selenium, beautifulsoup4, lxml
- openpyxl (опционально, для Excel)

## Использование

### Базовый запуск

```bash
python main.py --limit 50 --reports 100
```

### Параметры командной строки

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--limit` | Количество хакеров для сбора | 50 |
| `--reports` | Количество отчётов для сбора | 100 |
| `--headless` | Режим браузера (true/false) | true |
| `--export` | Форматы экспорта (json csv) | json csv |
| `--output` | Папка для результатов | data/processed |
| `--log-level` | Уровень логирования | INFO |

### Примеры

```bash
# Сбор топ-20 хакеров
python main.py --limit 20

# Запуск с видимым браузером
python main.py --headless false

# Экспорт только в JSON
python main.py --export json

# Debug логирование
python main.py --log-level DEBUG
```

## Структура проекта

```
workspace/
├── main.py                 # Точка входа CLI
├── config.yaml             # Конфигурация
├── requirements.txt        # Зависимости
├── src/
│   ├── models/
│   │   └── entities.py     # Модели данных
│   ├── clients/
│   │   └── hackerone_scraper.py  # Скрапер
│   ├── collectors/
│   │   └── data_collectors.py    # Коллекторы
│   ├── processors/
│   │   └── data_processors.py    # Обработчики
│   ├── analyzers/
│   │   └── data_analyzers.py     # Анализаторы
│   ├── exporters/
│   │   └── data_exporters.py     # Экспортёры
│   ├── config/
│   │   └── settings.py           # Настройки
│   └── utils/
│       └── helpers.py            # Утилиты
├── tests/
│   └── test_all.py         # Unit-тесты
├── data/
│   ├── raw/                # Сырые данные
│   ├── processed/          # Обработанные данные
│   └── debug/              # Debug HTML
└── logs/                   # Логи выполнения
```

## Модели данных

### HackerProfile
- username, reputation, signal, impact
- total_bounties, total_reports, accepted_reports
- acceptance_rate, country, skills, is_verified
- value_score, activity_score, quality_score, tier

### BugReport
- report_id, title, state, hacker_username
- program_name, bounty_amount, severity

### HackerValueAnalysis
- value_score, activity_score, quality_score, tier
- strengths, weaknesses, recommendations
- recruitment_priority

## Метрики

### Value Score (0-100)
```
value_score = 0.40 × norm(reputation) + 0.30 × norm(signal) + 0.30 × norm(impact)
```

### Activity Score (0-100)
```
activity_score = total_reports × 0.4 + acceptance_rate × 40 + is_verified × 20
```

### Quality Score (0-100)
```
quality_score = acceptance_rate × 50 + norm(avg_bounty) × 30 + norm(impact) × 20
```

### Tier Thresholds
| Score | Tier |
|-------|------|
| ≥ 80 | elite |
| ≥ 60 | premium |
| ≥ 40 | standard |
| < 40 | novice |

## Тестирование

```bash
python tests/test_all.py
```

## Обработка ошибок

- **ChromeNotAvailableError**: Если Google Chrome не установлен
- Rate limiting для защиты от блокировок
- Автоматическое закрытие ресурсов через контекстные менеджеры
- Логирование всех ошибок в файл

## Лицензия

MIT License

## Предупреждение

Скрапинг HackerOne может нарушать Условия Использования платформы. Используйте на свой риск и соблюдайте правила целевой платформы.