"""Метрики качества результата парсинга."""

import re


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return max(0.0, min(1.0, numerator / denominator))


def score_quality(text: str, semantic_blocks: list[dict]) -> dict:
    text = text or ""
    total_chars = len(text)
    words = re.findall(r"\w+", text, flags=re.UNICODE)

    non_printable_count = sum(
        1 for ch in text if ch not in "\n\r\t" and not ch.isprintable()
    )
    replacement_char_count = text.count("�")
    weird_symbols_count = len(re.findall(r"[□■▪•◊¤§¶]+", text))

    noise_ratio = _safe_ratio(
        non_printable_count + weird_symbols_count, max(total_chars, 1)
    )
    broken_ratio = _safe_ratio(replacement_char_count, max(total_chars, 1))

    text_completeness = 1.0 if total_chars >= 200 else _safe_ratio(total_chars, 200)

    block_count = len(semantic_blocks or [])
    table_blocks = sum(
        1 for b in semantic_blocks or [] if b.get("element_type") == "table"
    )
    table_coverage = (
        _safe_ratio(table_blocks, max(block_count, 1)) if block_count else 0.0
    )

    structure_score = 1.0 if block_count >= 3 else _safe_ratio(block_count, 3)

    overall_score = max(
        0.0,
        min(
            1.0,
            (0.35 * text_completeness)
            + (0.25 * structure_score)
            + (0.20 * (1 - noise_ratio))
            + (0.15 * (1 - broken_ratio))
            + (0.05 * (0.5 + table_coverage)),
        ),
    )

    return {
        "overall_score": round(overall_score, 4),
        "text_completeness": round(text_completeness, 4),
        "structure_score": round(structure_score, 4),
        "noise_ratio": round(noise_ratio, 4),
        "broken_chars_ratio": round(broken_ratio, 4),
        "table_coverage": round(table_coverage, 4),
        "char_count": total_chars,
        "word_count": len(words),
        "block_count": block_count,
    }
