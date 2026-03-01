# ─────────────────────────────────────────
# Stage 1: builder — установка зависимостей
# ─────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Системные зависимости для сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только манифест для кэширования слоя зависимостей
COPY pyproject.toml .
COPY src/ src/

# Устанавливаем пакет и все зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir ".[dev]"

# ─────────────────────────────────────────
# Stage 2: runtime — финальный образ
# ─────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Системные зависимости для работы парсеров
RUN apt-get update && apt-get install -y --no-install-recommends \
    # python-magic (определение MIME типов)
    libmagic1 \
    # lxml (парсинг XML/HTML)
    libxml2 \
    libxslt1.1 \
    # pdfplumber / PyPDF2 (работа с PDF)
    poppler-utils \
    # DJVU поддержка
    djvulibre-bin \
    # Кодировки
    locales \
    && rm -rf /var/lib/apt/lists/*

# UTF-8 локаль для корректной работы с текстом
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Копируем установленные пакеты из builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код
COPY src/ src/
COPY pyproject.toml .

# Папки для входных и выходных файлов
RUN mkdir -p /app/input /app/output

# Устанавливаем пакет в режиме editable
RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src

VOLUME ["/app/input", "/app/output"]

CMD ["parser-manager"]
