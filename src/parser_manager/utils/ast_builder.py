"""Построитель Document AST из flat semantic_blocks.

Преобразует плоский список блоков в дерево документа:

    Document
     ├── Section (heading level 1: "Introduction")
     │    ├── paragraph
     │    ├── table
     │    └── Section (heading level 2: "Background")
     │         └── paragraph
     └── paragraph  (блок до первого заголовка)
"""


def build_ast(semantic_blocks: list[dict]) -> dict:
    """
    Построить Document AST из flat-списка semantic_blocks.

    Returns:
        dict с полями type="document", children=[], meta={}
    """
    root: dict = {
        "type": "document",
        "children": [],
        "meta": {"total_blocks": len(semantic_blocks or [])},
    }

    if not semantic_blocks:
        return root

    # stack: list of (heading_level, node)  — level 0 = document root
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
            # pop stack until parent has a strictly lower heading level
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
