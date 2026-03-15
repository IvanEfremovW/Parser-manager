"""Экспорт ParsedContent в различные форматы: Markdown, JSON и читабельный отчет."""

from __future__ import annotations

import json
from textwrap import fill, indent
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from parser_manager.models.parsed_content import ParsedContent


def _meta(content: "ParsedContent") -> dict:
    return content.metadata if isinstance(content.metadata, dict) else {}


def _title(content: "ParsedContent") -> str:
    meta = _meta(content)
    title = str(meta.get("title") or "").strip()
    if title:
        return title
    fp = str(content.file_path).replace("\\", "/")
    return fp.rsplit("/", 1)[-1] or "Document"


def _file_name(content: "ParsedContent") -> str:
    fp = str(content.file_path).replace("\\", "/")
    return fp.rsplit("/", 1)[-1] or str(content.file_path)


def _fmt_number(value: object, digits: int = 2) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _fmt_percent(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.0f}%"
    return "-"


def _truncate(text: str, limit: int = 180) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_prose(text: str) -> str:
    chunks = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(chunks)


def _wrap_block(text: str, width: int = 92, prefix: str = "") -> str:
    normalized = _normalize_prose(text)
    paragraphs = [normalized] if normalized else []
    if not paragraphs:
        return ""
    wrapped = [fill(paragraph, width=width) for paragraph in paragraphs]
    return indent("\n".join(wrapped), prefix) if prefix else "\n".join(wrapped)


def _content_label(block: dict) -> str:
    page = block.get("page")
    btype = str(block.get("element_type", "paragraph")).capitalize()
    if page is None:
        return btype
    return f"Page {page} | {btype}"


def _iter_summary_rows(content: "ParsedContent") -> list[tuple[str, str]]:
    stats = content.doc_stats or {}
    quality = content.quality or {}
    metrics = content.file_metrics or {}
    meta = _meta(content)

    rows = [
        ("File", _file_name(content)),
        ("Format", str(content.format).upper()),
        ("Pages", str(meta.get("pages") or stats.get("pages") or "-")),
        ("Words", str(stats.get("word_count", 0))),
        ("Reading time", f"{stats.get('reading_time_min', 0)} min"),
        ("Blocks", str(metrics.get("semantic_blocks", len(content.semantic_blocks)))),
    ]

    if quality:
        rows.extend(
            [
                ("Quality", _fmt_number(quality.get("overall_score", "-"))),
                (
                    "Completeness",
                    _fmt_percent(quality.get("text_completeness")),
                ),
                ("Structure", _fmt_percent(quality.get("structure_score"))),
            ]
        )
    return rows


def to_markdown(content: "ParsedContent") -> str:
    """Конвертировать ParsedContent в Markdown-строку."""
    lines: list[str] = []

    meta = _meta(content)
    title = _title(content)
    lines.append(f"# {title}\n")

    lines.append(
        f"> File: `{_file_name(content)}`  \\n+> Format: `{str(content.format).upper()}`  \\n+> Pages: `{meta.get('pages') or content.doc_stats.get('pages', '-')}`"
    )
    lines.append("")

    stats = content.doc_stats
    quality = content.quality or {}

    lines.append("## Summary\n")
    for label, value in _iter_summary_rows(content):
        lines.append(f"- **{label}:** {value}")
    lines.append("")

    if quality:
        lines.append("## Quality\n")
        lines.append(f"- **Noise ratio:** {_fmt_percent(quality.get('noise_ratio'))}")
        lines.append(
            f"- **Broken chars:** {_fmt_percent(quality.get('broken_chars_ratio'))}"
        )
        lines.append(
            f"- **Table coverage:** {_fmt_percent(quality.get('table_coverage'))}"
        )
        lines.append("")

    lines.append("## Content\n")

    for block in content.semantic_blocks:
        btype = block.get("element_type", "paragraph")
        text = (block.get("content") or "").strip()
        blevel = int(block.get("level") or 0)

        if not text:
            continue

        normalized_text = _normalize_prose(text) if btype != "table" else text

        if btype == "heading":
            hashes = "#" * max(1, min(blevel or 2, 6))
            lines.append(f"{hashes} {normalized_text}\n")
        elif btype == "list":
            for item in [line.strip(" -") for line in text.splitlines() if line.strip()]:
                lines.append(f"- {item}")
            lines.append("")
        elif btype == "table":
            lines.append(f"### {_content_label(block)}\n")
            lines.append(f"```text\n{text}\n```\n")
        elif btype == "link":
            href = (block.get("metadata") or {}).get("href", "")
            lines.append(
                f"- [{normalized_text}]({href})" if href else f"- {normalized_text}"
            )
        else:
            lines.append(f"### {_content_label(block)}\n")
            lines.append(f"{normalized_text}\n")

    return "\n".join(lines)


def to_report(content: "ParsedContent") -> str:
    """Конвертировать ParsedContent в человеко-ориентированный текстовый отчет."""
    title = _title(content)
    stats = content.doc_stats or {}
    quality = content.quality or {}
    metrics = content.file_metrics or {}
    lines: list[str] = [title, "=" * len(title), ""]

    lines.append("Summary")
    lines.append("-------")
    key_width = max(len(label) for label, _ in _iter_summary_rows(content))
    for label, value in _iter_summary_rows(content):
        lines.append(f"{label:<{key_width}} : {value}")
    lines.append("")

    if quality:
        lines.append("Quality")
        lines.append("-------")
        lines.append(f"Noise ratio    : {_fmt_percent(quality.get('noise_ratio'))}")
        lines.append(
            f"Broken chars   : {_fmt_percent(quality.get('broken_chars_ratio'))}"
        )
        lines.append(
            f"Table coverage : {_fmt_percent(quality.get('table_coverage'))}"
        )
        lines.append("")

    lines.append("Document Stats")
    lines.append("--------------")
    lines.append(f"Characters     : {stats.get('char_count', 0)}")
    lines.append(f"Sentences      : {stats.get('sentence_count', 0)}")
    lines.append(f"Paragraphs     : {stats.get('paragraph_count', 0)}")
    lines.append(f"Tables         : {stats.get('table_count', 0)}")
    lines.append(f"Headings       : {stats.get('heading_count', 0)}")
    lines.append(f"Lists          : {stats.get('list_count', 0)}")
    lines.append(f"Avg block size : {metrics.get('avg_block_length', 0)}")
    lines.append("")

    if content.semantic_blocks:
        lines.append("Quick Preview")
        lines.append("-------------")
        for index, block in enumerate(content.semantic_blocks[:3], start=1):
            preview = _truncate(_normalize_prose(str(block.get("content") or "")))
            label = _content_label(block)
            lines.append(f"{index}. {label}: {preview}")
        lines.append("")

    lines.append("Content")
    lines.append("-------")
    for block in content.semantic_blocks:
        text = str(block.get("content") or "").strip()
        if not text:
            continue

        label = _content_label(block)
        lines.append(label)
        lines.append("~" * len(label))

        btype = str(block.get("element_type", "paragraph"))
        if btype == "table":
            lines.append(indent(text, "  "))
        elif btype == "list":
            items = [line.strip(" -") for line in text.splitlines() if line.strip()]
            for item in items:
                lines.append(f"  - {_truncate(item, limit=400)}")
        else:
            wrapped = _wrap_block(_normalize_prose(text), prefix="  ")
            if wrapped:
                lines.append(wrapped)
        lines.append("")

    if not content.semantic_blocks and content.text:
        lines.append(_wrap_block(content.text))

    return "\n".join(lines).rstrip()


def to_json(content: "ParsedContent", pretty: bool = True) -> str:
    """Конвертировать ParsedContent в JSON-строку."""
    return json.dumps(
        content.to_dict(), ensure_ascii=False, indent=2 if pretty else None
    )


_EXPORTERS: dict[str, Callable[..., str]] = {
    "json": to_json,
    "md": to_markdown,
    "markdown": to_markdown,
    "report": to_report,
    "txt": to_report,
    "text": to_report,
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
