"""Экспорт ParsedContent в различные форматы: Markdown, JSON."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from parser_manager.models.parsed_content import ParsedContent


def to_markdown(content: "ParsedContent") -> str:
    """Конвертировать ParsedContent в Markdown-строку."""
    lines: list[str] = []

    meta = content.metadata if isinstance(content.metadata, dict) else {}
    title = meta.get("title") or ""
    fp = str(content.file_path).replace("\\", "/")
    file_name = fp.rsplit("/", 1)[-1]
    lines.append(f"# {title or file_name}\n")

    stats = content.doc_stats
    if stats.get("word_count"):
        lines.append(
            f"*Слов: {stats['word_count']} | "
            f"Абзацев: {stats['paragraph_count']} | "
            f"Время чтения: {stats['reading_time_min']} мин*\n"
        )

    lines.append("---\n")

    for block in content.semantic_blocks:
        btype = block.get("element_type", "paragraph")
        text = (block.get("content") or "").strip()
        blevel = int(block.get("level") or 0)

        if not text:
            continue

        if btype == "heading":
            hashes = "#" * max(1, min(blevel or 2, 6))
            lines.append(f"{hashes} {text}\n")
        elif btype == "list":
            lines.append(f"- {text}")
        elif btype == "table":
            lines.append(f"\n```\n{text}\n```\n")
        elif btype == "link":
            href = (block.get("metadata") or {}).get("href", "")
            lines.append(f"[{text}]({href})" if href else text)
        else:
            lines.append(f"\n{text}\n")

    return "\n".join(lines)


def to_json(content: "ParsedContent", pretty: bool = True) -> str:
    """Конвертировать ParsedContent в JSON-строку."""
    return json.dumps(
        content.to_dict(), ensure_ascii=False, indent=2 if pretty else None
    )


_EXPORTERS: dict[str, Callable[..., str]] = {
    "json": to_json,
    "md": to_markdown,
    "markdown": to_markdown,
}


def export_content(content: "ParsedContent", fmt: str, **kwargs: object) -> str:
    """
    Экспортировать ParsedContent в заданный формат.

    Args:
        content: результат парсинга
        fmt: 'json', 'md' или 'markdown'
        **kwargs: доп. аргументы (например pretty=False для json)

    Raises:
        ValueError: если формат не поддерживается
    """
    fmt = fmt.lower()
    fn = _EXPORTERS.get(fmt)
    if fn is None:
        supported = ", ".join(sorted({*_EXPORTERS}))
        raise ValueError(f"Неизвестный формат экспорта '{fmt}'. Доступные: {supported}")
    if fmt == "json":
        return fn(content, **kwargs)
    return fn(content)
