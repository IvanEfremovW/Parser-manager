"""
Юнит-тесты для утилит semantic JSON.

Тест-кейсы:
- TC-UTIL-001: Нормализация блоков
"""

from parser_manager.utils.semantic_json import (
    ALLOWED_BLOCK_TYPES,
    derive_semantic_blocks,
    normalize_block,
    normalize_structure,
    semantic_summary,
)


class TestNormalizeBlock:
    """Тесты для функции normalize_block."""

    def test_normalize_block_basic(self):
        """Тест базовой нормализации блока."""
        block = {
            "content": "Test content",
            "element_type": "paragraph",
        }

        result = normalize_block(block)

        assert result["content"] == "Test content"
        assert result["element_type"] == "paragraph"
        assert result["level"] == 0
        assert result["position"] is None
        assert result["page"] is None
        assert result["metadata"] == {}

    def test_normalize_block_preserves_all_fields(self):
        """Тест сохранения всех полей."""
        block = {
            "content": "Heading",
            "element_type": "heading",
            "level": 2,
            "position": {"x": 100, "y": 200},
            "page": 5,
            "metadata": {"source": "test"},
        }

        result = normalize_block(block)

        assert result["level"] == 2
        assert result["position"] == {"x": 100, "y": 200}
        assert result["page"] == 5
        assert result["metadata"] == {"source": "test"}

    def test_normalize_block_invalid_element_type(self):
        """Тест что invalid element_type становится paragraph по умолчанию."""
        block = {
            "content": "Test",
            "element_type": "invalid_type",
        }

        result = normalize_block(block)

        assert result["element_type"] == "paragraph"

    def test_normalize_block_element_type_case_insensitive(self):
        """Тест что element_type нормализуется к нижнему регистру."""
        block = {
            "content": "Test",
            "element_type": "HEADING",
        }

        result = normalize_block(block)

        assert result["element_type"] == "heading"

    def test_normalize_block_all_allowed_types(self):
        """Тест все разрешённые типы блоков сохраняются."""
        for block_type in ALLOWED_BLOCK_TYPES:
            block = {
                "content": "Test",
                "element_type": block_type,
            }

            result = normalize_block(block)

            assert result["element_type"] == block_type

    def test_normalize_block_strips_content(self):
        """Тест что content обрезается."""
        block = {
            "content": "  Test content with spaces  ",
            "element_type": "paragraph",
        }

        result = normalize_block(block)

        assert result["content"] == "Test content with spaces"

    def test_normalize_block_empty_content(self):
        """Тест обработки пустого content."""
        block = {
            "content": "",
            "element_type": "paragraph",
        }

        result = normalize_block(block)

        assert result["content"] == ""

    def test_normalize_block_none_content(self):
        """Тест обработки None content."""
        block = {
            "content": None,
            "element_type": "paragraph",
        }

        result = normalize_block(block)

        assert result["content"] == ""

    def test_normalize_block_level_conversion(self):
        """Тест что level конвертируется в int."""
        block = {
            "content": "Heading",
            "element_type": "heading",
            "level": "3",
        }

        result = normalize_block(block)

        assert result["level"] == 3

    def test_normalize_block_none_level(self):
        """Тест что None level становится 0."""
        block = {
            "content": "Test",
            "element_type": "paragraph",
            "level": None,
        }

        result = normalize_block(block)

        assert result["level"] == 0

    def test_normalize_block_default_page(self):
        """Тест параметра default page."""
        block = {
            "content": "Test",
            "element_type": "paragraph",
        }

        result = normalize_block(block, default_page=10)

        assert result["page"] == 10

    def test_normalize_block_page_override(self):
        """Тест что page блока переопределяет default."""
        block = {
            "content": "Test",
            "element_type": "paragraph",
            "page": 5,
        }

        result = normalize_block(block, default_page=10)

        assert result["page"] == 5

    def test_normalize_block_none_metadata(self):
        """Тест что None metadata становится пустым dict."""
        block = {
            "content": "Test",
            "element_type": "paragraph",
            "metadata": None,
        }

        result = normalize_block(block)

        assert result["metadata"] == {}


class TestNormalizeStructure:
    """Тесты для функции normalize_structure."""

    def test_normalize_structure_basic(self):
        """Тест базовой нормализации структуры."""
        structure = [
            {"content": "Heading", "element_type": "heading", "level": 1},
            {"content": "Paragraph", "element_type": "paragraph"},
        ]

        result = normalize_structure(structure)

        assert len(result) == 2
        assert result[0]["element_type"] == "heading"
        assert result[1]["element_type"] == "paragraph"

    def test_normalize_structure_empty(self):
        """Тест пустой структуры."""
        result = normalize_structure([])

        assert result == []

    def test_normalize_structure_none(self):
        """Тест None структуры."""
        result = normalize_structure(None)

        assert result == []

    def test_normalize_structure_filters_empty_content(self):
        """Тест что блоки с пустым content фильтруются."""
        structure = [
            {"content": "Valid", "element_type": "paragraph"},
            {"content": "", "element_type": "paragraph"},
            {"content": "   ", "element_type": "paragraph"},
        ]

        result = normalize_structure(structure)

        assert len(result) == 1
        assert result[0]["content"] == "Valid"

    def test_normalize_structure_filters_non_dicts(self):
        """Тест что не-dict элементы фильтруются."""
        structure = [
            {"content": "Valid", "element_type": "paragraph"},
            "not a dict",
            None,
            123,
            {"content": "Also valid", "element_type": "heading"},
        ]

        result = normalize_structure(structure)

        assert len(result) == 2

    def test_normalize_structure_normalizes_each_block(self):
        """Тест что каждый блок нормализуется."""
        structure = [
            {"content": "  Spaced  ", "element_type": "INVALID"},
        ]

        result = normalize_structure(structure)

        assert result[0]["content"] == "Spaced"
        assert result[0]["element_type"] == "paragraph"


class TestDeriveSemanticBlocks:
    """Тесты для функции derive_semantic_blocks."""

    def test_derive_semantic_blocks_from_structure(self):
        """Тест получения блоков из структуры."""
        text = "Some text"
        structure = [
            {"content": "Heading", "element_type": "heading"},
            {"content": "Paragraph", "element_type": "paragraph"},
        ]

        result = derive_semantic_blocks(text, structure)

        assert len(result) == 2
        assert result[0]["content"] == "Heading"
        assert result[1]["content"] == "Paragraph"

    def test_derive_semantic_blocks_fallback_to_text(self):
        """Тест fallback на текст когда структура пустая."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        structure = []

        result = derive_semantic_blocks(text, structure)

        assert len(result) == 3
        assert all(b["element_type"] == "paragraph" for b in result)

    def test_derive_semantic_blocks_fallback_none_structure(self):
        """Тест fallback когда структура None."""
        text = "Paragraph 1.\n\nParagraph 2."

        result = derive_semantic_blocks(text, None)

        assert len(result) == 2

    def test_derive_semantic_blocks_empty_text(self):
        """Тест с пустым текстом."""
        result = derive_semantic_blocks("", [])

        assert result == []

    def test_derive_semantic_blocks_structure_takes_precedence(self):
        """Тест что структура используется даже когда текст доступен."""
        text = "Different text"
        structure = [{"content": "Structure content", "element_type": "paragraph"}]

        result = derive_semantic_blocks(text, structure)

        assert result[0]["content"] == "Structure content"


class TestSemanticSummary:
    """Тесты для функции semantic_summary."""

    def test_semantic_summary_basic(self):
        """Тест базового semantic summary."""
        blocks = [
            {"element_type": "heading"},
            {"element_type": "paragraph"},
            {"element_type": "paragraph"},
            {"element_type": "table"},
        ]

        result = semantic_summary(blocks)

        assert result["total_blocks"] == 4
        assert result["heading_blocks"] == 1
        assert result["paragraph_blocks"] == 2
        assert result["table_blocks"] == 1
        assert result["list_blocks"] == 0
        assert result["link_blocks"] == 0

    def test_semantic_summary_empty(self):
        """Тест summary пустых блоков."""
        result = semantic_summary([])

        assert result["total_blocks"] == 0
        assert result["heading_blocks"] == 0

    def test_semantic_summary_none_blocks(self):
        """Тест summary None блоков."""
        result = semantic_summary(None)

        assert result["total_blocks"] == 0

    def test_semantic_summary_pages_detected(self):
        """Тест подсчёта pages_detected."""
        blocks = [
            {"element_type": "paragraph", "page": 1},
            {"element_type": "paragraph", "page": 1},
            {"element_type": "paragraph", "page": 2},
            {"element_type": "paragraph", "page": 3},
            {"element_type": "paragraph", "page": None},
        ]

        result = semantic_summary(blocks)

        assert result["pages_detected"] == 3

    def test_semantic_summary_all_block_types(self):
        """Тест summary со всеми типами блоков."""
        blocks = [
            {"element_type": "heading"},
            {"element_type": "paragraph"},
            {"element_type": "table"},
            {"element_type": "list"},
            {"element_type": "link"},
        ]

        result = semantic_summary(blocks)

        assert result["heading_blocks"] == 1
        assert result["paragraph_blocks"] == 1
        assert result["table_blocks"] == 1
        assert result["list_blocks"] == 1
        assert result["link_blocks"] == 1

    def test_semantic_summary_missing_element_type(self):
        """Тест обработки блоков без element_type."""
        blocks = [
            {"content": "Test"},
            {"element_type": "paragraph"},
        ]

        result = semantic_summary(blocks)

        # Missing element_type defaults to paragraph in Counter
        assert result["total_blocks"] == 2
