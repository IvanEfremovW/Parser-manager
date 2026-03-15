"""Построитель Document AST из плоского списка semantic_blocks.

Преобразует плоский список блоков в дерево документа:

    Document
     ├── Section (заголовок уровня 1: "Введение")
     │    ├── paragraph
     │    ├── table
     │    └── Section (заголовок уровня 2: "Предпосылки")
     │         └── paragraph
     └── paragraph (блок до первого заголовка)
"""


def build_ast(semantic_blocks: list[dict]) -> dict:
    """
    Построить Document AST из плоского списка semantic_blocks.

    Возвращает:
        dict с полями type="document", children=[], meta={}
    """
    root: dict = {
        "type": "document",
        "children": [],
        "meta": {"total_blocks": len(semantic_blocks or [])},
    }

    if not semantic_blocks:
        return root

    # Стек: список пар (уровень_заголовка, узел), где 0 — корень документа
    stack: list[tuple[int, dict]] = [(0, root)]

    for block in semantic_blocks:
        btype = block.get("element_type", "paragraph")
        content = (block.get("content") or "").strip()
        level = int(block.get("level") or 0)
        page = block.get("page")
        meta = block.get("metadata") or {}

        if btype == "heading":
            heading_level = level if level > 0 else 1
            section: dict = {
                "type": "section",
                "title": content,
                "level": heading_level,
                "page": page,
                "children": [],
            }
            # Снимаем элементы стека, пока у родителя уровень не станет строго меньше
            while len(stack) > 1 and stack[-1][0] >= heading_level:
                stack.pop()
            stack[-1][1]["children"].append(section)
            stack.append((heading_level, section))
        else:
            leaf: dict = {
                "type": btype,
                "content": content,
                "page": page,
            }
            if meta:
                leaf["metadata"] = meta
            stack[-1][1]["children"].append(leaf)

    return root
