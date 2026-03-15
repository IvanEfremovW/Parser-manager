"""Статистика документа: счётчики слов, абзацев, заголовков, время чтения."""

import re
from math import ceil

_WORDS_PER_MINUTE = 200  # средняя скорость чтения


def compute_doc_stats(text: str, semantic_blocks: list[dict], metadata: dict) -> dict:
    """
    Вычислить статистику документа.

    Returns:
        dict с полями: word_count, char_count, sentence_count, paragraph_count,
        heading_count, table_count, list_count, link_count,
        reading_time_min, reading_time_sec, pages
    """
    clean_text = text or ""
    words = re.findall(r"\b\w+\b", clean_text)
    word_count = len(words)
    char_count = len(re.sub(r"\s", "", clean_text))
    sentence_count = sum(
        1 for s in re.split(r"[.!?]+", clean_text) if s.strip()
    )

    blocks = semantic_blocks or []
    paragraph_count = sum(1 for b in blocks if b.get("element_type") == "paragraph")
    heading_count = sum(1 for b in blocks if b.get("element_type") == "heading")
    table_count = sum(1 for b in blocks if b.get("element_type") == "table")
    list_count = sum(1 for b in blocks if b.get("element_type") == "list")
    link_count = sum(1 for b in blocks if b.get("element_type") == "link")

    reading_time_min = round(word_count / _WORDS_PER_MINUTE, 1)
    reading_time_sec = ceil(reading_time_min * 60)

    pages: int | None = None
    if isinstance(metadata, dict):
        raw_pages = metadata.get("pages")
        if raw_pages is not None:
            try:
                pages = int(raw_pages)
            except (TypeError, ValueError):
                pages = None

    return {
        "word_count": word_count,
        "char_count": char_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "heading_count": heading_count,
        "table_count": table_count,
        "list_count": list_count,
        "link_count": link_count,
        "reading_time_min": reading_time_min,
        "reading_time_sec": reading_time_sec,
        "pages": pages,
    }
