"""Утилиты для унификации semantic JSON блоков."""

from collections import Counter

ALLOWED_BLOCK_TYPES = {"heading", "paragraph", "table", "list", "link"}


def normalize_block(block: dict, default_page: int | None = None) -> dict:
    element_type = str(block.get("element_type", "paragraph")).lower()
    if element_type not in ALLOWED_BLOCK_TYPES:
        element_type = "paragraph"

    content_raw = block.get("content")
    content = str(content_raw).strip() if content_raw is not None else ""
    level = int(block.get("level", 0) or 0)
    position = block.get("position") or None
    page = block.get("page", default_page)

    metadata_raw = block.get("metadata")
    metadata = metadata_raw if metadata_raw is not None else {}

    return {
        "content": content,
        "element_type": element_type,
        "level": level,
        "position": position,
        "page": page,
        "metadata": metadata,
    }


def normalize_structure(structure: list[dict]) -> list[dict]:
    blocks: list[dict] = []
    for raw in structure or []:
        if not isinstance(raw, dict):
            continue
        normalized = normalize_block(raw)
        if normalized["content"]:
            blocks.append(normalized)
    return blocks


def derive_semantic_blocks(text: str, structure: list[dict]) -> list[dict]:
    blocks = normalize_structure(structure)
    if blocks:
        return blocks

    fallback = []
    for paragraph in [p.strip() for p in (text or "").split("\n\n") if p.strip()]:
        fallback.append(
            {
                "content": paragraph,
                "element_type": "paragraph",
                "level": 0,
                "position": None,
                "page": None,
                "metadata": {},
            }
        )
    return fallback


def semantic_summary(blocks: list[dict]) -> dict:
    if not blocks:
        blocks = []
    counts = Counter(b.get("element_type", "paragraph") for b in blocks)
    return {
        "total_blocks": len(blocks),
        "heading_blocks": counts.get("heading", 0),
        "paragraph_blocks": counts.get("paragraph", 0),
        "table_blocks": counts.get("table", 0),
        "list_blocks": counts.get("list", 0),
        "link_blocks": counts.get("link", 0),
        "pages_detected": len(
            {b.get("page") for b in blocks if b.get("page") is not None}
        ),
    }
