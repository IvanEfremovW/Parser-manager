# Parser Manager

Унифицированный парсинг `html/pdf/docx/doc/djvu` в единый semantic JSON для RAG/LLM.

## Архитектура

- `core/`
	- `BaseParser` — контракт парсеров.
	- `ParserFactory` — выбор парсера по расширению.
- `parsers/`
	- Форматные парсеры: `HtmlParser`, `PdfParser`, `DocxParser`, `DocParser`, `DjvuParser`.
	- Авто-регистрация парсеров в реестре.
- `models/`
	- `ParsedContent` — единая модель результата.
	- `DocumentMetadata`, `TextElement`, доменные исключения.
- `utils/`
	- `semantic_json` — нормализация блоков (`heading/paragraph/table/list/link`) + page/position.
	- `quality` — качество парсинга (`overall_score`, `noise_ratio`, `broken_chars_ratio`, `table_coverage`).
	- `file_metrics` — метрики файла/контента после парсинга.
- `api/`
	- FastAPI, async job queue, webhook callback.

## Выходной JSON

Каждый результат содержит:

- `structure` — сырой структурный вывод парсера.
- `semantic_blocks` — унифицированные блоки для downstream-пайплайнов.
- `quality` — quality scoring.
- `file_metrics` — метрики по файлу и извлечённому тексту.

## Docker

### 1) API (основной режим)

```bash
docker compose up --build api
```

API будет доступен на `http://localhost:8000`.

- Health: `GET /health`
- Создать job: `POST /jobs/parse` (multipart: `file`, optional `webhook_url`)
- Статус: `GET /jobs/{job_id}`
- Результат: `GET /jobs/{job_id}/result`

### 2) CLI через Docker

```bash
docker compose --profile cli run --rm parser-cli --file /app/input/sample.html --output /app/output/result.json --pretty
```

### 3) Тесты в Docker

```bash
docker compose --profile test run --rm tests
```

### 4) Dev shell

```bash
docker compose --profile dev run --rm dev
```

## Локальный запуск (без Docker)

```bash
python -m parser_manager --list-formats
python -m parser_manager --file ./input/sample.html --output ./output/result.json --pretty
parser-manager-api
```

## Архитектурные заметки

- PDF использует quality-aware fallback (`pdfplumber` -> `PyPDF2`, если качество ниже порога).
- Очередь API in-memory (подходит для MVP и single-instance). Для production нужен внешний брокер/хранилище статусов.
- Webhook отправляется после финализации job (`done`/`failed`).
