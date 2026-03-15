# Parser Manager

Унифицированный парсинг `html/pdf/docx/doc/djvu` в единый semantic JSON для RAG/LLM.  
Поддерживает CLI, REST API с async-очередью и webhook-уведомлениями.

---

## Поддерживаемые форматы

| Расширение | Парсер |
|---|---|
| `.html`, `.htm` | `HtmlParser` (BeautifulSoup + lxml) |
| `.pdf` | `PdfParser` (pdfplumber → PyPDF2 fallback) |
| `.docx` | `DocxParser` (python-docx) |
| `.doc` | `DocParser` (oletools) |
| `.djvu` | `DjvuParser` |

---

## Выходная модель (`ParsedContent`)

| Поле | Описание |
|---|---|
| `text` | Извлечённый plain-text |
| `semantic_blocks` | Унифицированные блоки: `heading / paragraph / table / list / link` |
| `quality` | Оценка качества: `overall_score`, `noise_ratio`, `broken_chars_ratio`, `text_completeness`, `structure_score` |
| `doc_stats` | Статистика документа: `word_count`, `sentence_count`, `paragraph_count`, `pages`, `reading_time_min` |
| `file_metrics` | Размер файла, длина текста, кол-во блоков |
| `ast` | Дерево документа `Document → Section → leaf` |
| `metadata` | Заголовок, автор, дата создания и др. |

---

## Форматы экспорта

| Формат | Ключ | Описание |
|---|---|---|
| JSON | `json` | Полная машино-читаемая структура |
| Markdown | `md` | Структурированный Markdown с метаданными и quality-секцией |
| Отчёт | `report` | Человеко-читаемый текстовый отчёт (Summary / Quality / Content) |

---

## CLI

```bash
# Показать поддерживаемые форматы
python -m parser_manager --list-formats

# Распарсить файл → вывод читабельного отчёта в консоль
python -m parser_manager --file ./input/sample.pdf

# Сохранить результат в JSON
python -m parser_manager --file ./input/sample.pdf --output ./output/result.json

# Pretty-print JSON
python -m parser_manager --file ./input/sample.pdf --output ./output/result.json --pretty

# Явно выбрать формат экспорта (json | md | report)
python -m parser_manager --file ./input/sample.pdf --export-format md

# Показать служебные логи парсинга
python -m parser_manager --file ./input/sample.pdf --verbose

# Показать версию
python -m parser_manager --version
```

> **Поведение по умолчанию:** при выводе в консоль — `report`; при записи в файл (`--output`) — `json`.

---

## REST API

Запуск:

```bash
parser-manager-api
# или
uvicorn parser_manager.api.app:app --host 0.0.0.0 --port 8000
```

### Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/` | Описание сервиса, список форматов и эндпоинтов |
| `GET` | `/health` | Статус сервиса + размер очереди |
| `POST` | `/jobs/parse` | Загрузить файл → получить `job_id` |
| `GET` | `/jobs/{id}` | Статус задачи (`queued / processing / done / failed`) |
| `GET` | `/jobs/{id}/result` | Полный результат (JSON) после завершения |
| `GET` | `/jobs/{id}/stats` | Только `doc_stats` задачи |
| `GET` | `/jobs/{id}/ast` | Только Document AST задачи |
| `GET` | `/jobs/{id}/export/{fmt}` | Экспорт в `json`, `md` или `report` |

### Примеры (curl)

```bash
# Загрузить файл и получить job_id
curl.exe -X POST "http://localhost:8000/jobs/parse" -F "file=@./input/sample.pdf"

# Проверить статус
curl.exe "http://localhost:8000/jobs/{job_id}"

# Получить полный JSON-результат
curl.exe "http://localhost:8000/jobs/{job_id}/result"

# Получить читабельный отчёт
curl.exe "http://localhost:8000/jobs/{job_id}/export/report"

# Загрузить с webhook
curl.exe -X POST "http://localhost:8000/jobs/parse" \
  -F "file=@./input/sample.pdf" \
  -F "webhook_url=https://example.com/hook"
```

> **Windows PowerShell:** используйте `curl.exe` вместо `curl` (алиас `Invoke-WebRequest`).

---

## Docker

### API (основной режим)

```bash
docker compose up --build api
```

API доступен на `http://localhost:8000`.

### CLI через Docker

```bash
docker compose --profile cli run --rm parser-cli \
  --file /app/input/sample.html \
  --output /app/output/result.json \
  --pretty
```

### Тесты

```bash
docker compose --profile test run --rm tests
```

### Dev shell

```bash
docker compose --profile dev run --rm dev
```

---

## Архитектура

```
src/parser_manager/
├── core/
│   ├── base_parser.py      # BaseParser — контракт всех парсеров
│   └── parser_factory.py   # ParserFactory — выбор парсера по расширению
├── parsers/
│   └── documents/          # HtmlParser, PdfParser, DocxParser, DocParser, DjvuParser
├── models/
│   ├── parsed_content.py   # ParsedContent — единая модель результата
│   └── exceptions.py       # Доменные исключения
├── utils/
│   ├── exporters.py        # to_json / to_markdown / to_report
│   ├── semantic_json.py    # Нормализация semantic_blocks
│   ├── quality.py          # Quality scoring
│   └── file_metrics.py     # Метрики файла/контента
├── api/
│   ├── app.py              # FastAPI приложение
│   ├── jobs.py             # Async job queue
│   └── service.py          # Sync-воркер парсинга
└── __init__.py             # CLI entry point
```

---

## Архитектурные заметки

- PDF использует quality-aware fallback: `pdfplumber` → `PyPDF2`, если качество ниже порога.
- Очередь API in-memory (подходит для MVP и single-instance). Для production — нужен внешний брокер.
- Webhook отправляется POST-запросом после финализации job (`done` / `failed`).
- Логи парсинга (pdfminer/pdfplumber) заглушены по умолчанию; включить через `--verbose`.
