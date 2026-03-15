"""Метрики файла и результата после парсинга."""

from pathlib import Path


def collect_file_metrics(
    file_path: str, semantic_blocks: list[dict], text: str
) -> dict:
    path = Path(file_path)
    size = path.stat().st_size if path.exists() else 0

    block_lengths = [
        len((block.get("content") or "").strip()) for block in semantic_blocks or []
    ]

    return {
        "file_name": path.name,
        "extension": path.suffix.lower(),
        "file_size_bytes": size,
        "text_length": len(text or ""),
        "semantic_blocks": len(semantic_blocks or []),
        "avg_block_length": round(sum(block_lengths) / len(block_lengths), 2)
        if block_lengths
        else 0,
        "max_block_length": max(block_lengths) if block_lengths else 0,
    }
