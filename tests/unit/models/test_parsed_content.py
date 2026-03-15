"""
Юнит-тесты для моделей ParsedContent, DocumentMetadata и TextElement.

Тест-кейсы:
- TC-MODEL-001: Создание ParsedContent
- TC-MODEL-002: Валидация ParsedContent
"""

import pytest
from datetime import datetime
from pathlib import Path

from parser_manager.models import ParsedContent, DocumentMetadata, TextElement


class TestDocumentMetadata:
    """Тесты для модели DocumentMetadata."""

    def test_create_metadata_with_all_fields(self, sample_metadata: DocumentMetadata):
        """Тест создания метаданных со всеми полями."""
        assert sample_metadata.title == "Test Title"
        assert sample_metadata.author == "Test Author"
        assert sample_metadata.subject == "Test Subject"
        assert sample_metadata.pages == 10
        assert sample_metadata.language == "en"
        assert sample_metadata.encoding == "UTF-8"

    def test_create_metadata_minimal(self):
        """Тест создания метаданных с минимальными полями."""
        metadata = DocumentMetadata()

        assert metadata.title is None
        assert metadata.author is None
        assert metadata.custom_fields == {}

    def test_metadata_to_dict(self, sample_metadata: DocumentMetadata):
        """Тест конвертации метаданных в словарь."""
        result = sample_metadata.to_dict()

        assert result["title"] == "Test Title"
        assert result["author"] == "Test Author"
        assert result["pages"] == 10
        assert result["custom_field"] == "custom_value"

    def test_metadata_to_dict_datetime_format(self):
        """Тест форматирования datetime полей как ISO строк."""
        metadata = DocumentMetadata(
            creation_date=datetime(2024, 1, 15, 10, 30, 0),
            modification_date=datetime(2024, 1, 16, 14, 45, 0),
        )

        result = metadata.to_dict()

        assert result["creation_date"] == "2024-01-15T10:30:00"
        assert result["modification_date"] == "2024-01-16T14:45:00"

    def test_metadata_to_dict_none_datetime(self):
        """Тест что None datetime поля остаются None."""
        metadata = DocumentMetadata(creation_date=None)
        result = metadata.to_dict()

        assert result["creation_date"] is None

    def test_metadata_custom_fields_merged(self):
        """Тест что custom поля объединяются в результат."""
        metadata = DocumentMetadata(
            title="Test",
            custom_fields={"key1": "value1", "key2": "value2"},
        )

        result = metadata.to_dict()

        assert result["title"] == "Test"
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"


class TestTextElement:
    """Тесты для модели TextElement."""

    def test_create_text_element_minimal(self):
        """Тест создания текстового элемента с минимальными полями."""
        element = TextElement(content="Test content", element_type="paragraph")

        assert element.content == "Test content"
        assert element.element_type == "paragraph"
        assert element.level == 0
        assert element.style == {}
        assert element.position is None
        assert element.page is None
        assert element.metadata == {}

    def test_create_text_element_full(self):
        """Тест создания текстового элемента со всеми полями."""
        element = TextElement(
            content="Heading",
            element_type="heading",
            level=1,
            style={"bold": True, "size": 24},
            position={"x": 100, "y": 200},
            page=5,
            metadata={"source": "test"},
        )

        assert element.level == 1
        assert element.style == {"bold": True, "size": 24}
        assert element.position == {"x": 100, "y": 200}
        assert element.page == 5

    def test_text_element_to_dict(self, sample_text_elements: list[TextElement]):
        """Тест конвертации текстового элемента в словарь."""
        element = sample_text_elements[0]
        result = element.to_dict()

        assert result["content"] == "Main Heading"
        assert result["element_type"] == "heading"
        assert result["level"] == 1
        assert result["page"] == 1

    def test_text_element_all_types(self):
        """Тест создания элементов всех поддерживаемых типов."""
        types = ["heading", "paragraph", "table", "list", "link"]

        for elem_type in types:
            element = TextElement(content="Test", element_type=elem_type)
            assert element.element_type == elem_type

    def test_text_element_link_metadata(self):
        """Тест элемента ссылки с href метаданными."""
        element = TextElement(
            content="Click here",
            element_type="link",
            metadata={"href": "https://example.com"},
        )

        result = element.to_dict()
        assert result["metadata"]["href"] == "https://example.com"


class TestParsedContent:
    """Тесты для модели ParsedContent."""

    def test_create_parsed_content_success(
        self, sample_parsed_content: ParsedContent, sample_html_file: Path
    ):
        """Тест TC-MODEL-001: Создание ParsedContent с success=True."""
        assert sample_parsed_content.success is True
        assert sample_parsed_content.format == "html"
        assert sample_parsed_content.error is None

    def test_create_parsed_content_validation_error(self, temp_dir: Path):
        """Тест TC-MODEL-002: Ошибка валидации когда success=False без error."""
        with pytest.raises(ValueError) as exc_info:
            ParsedContent(
                file_path=str(temp_dir / "test.html"),
                format="html",
                text="",
                metadata={},
                structure=[],
                semantic_blocks=[],
                quality={},
                file_metrics={},
                raw_data={},
                success=False,
                error=None,
            )

        assert "error" in str(exc_info.value).lower()

    def test_create_parsed_content_unsupported_format(self, temp_dir: Path):
        """Тест что неподдерживаемый формат выбрасывает ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ParsedContent(
                file_path=str(temp_dir / "test.xyz"),
                format="unsupported_format",
                text="",
                metadata={},
                structure=[],
                semantic_blocks=[],
                quality={},
                file_metrics={},
                raw_data={},
                success=True,
            )

        assert "Неподдерживаемый формат" in str(exc_info.value)

    def test_create_parsed_content_supported_formats(self, temp_dir: Path):
        """Тест создания ParsedContent со всеми поддерживаемыми форматами."""
        supported = ["html", "pdf", "docx", "doc", "djvu"]

        for fmt in supported:
            content = ParsedContent(
                file_path=str(temp_dir / f"test.{fmt}"),
                format=fmt,
                text="test",
                metadata={},
                structure=[],
                semantic_blocks=[],
                quality={},
                file_metrics={},
                raw_data={},
                success=True,
            )
            assert content.format == fmt

    def test_parsed_content_text_length(self, sample_parsed_content: ParsedContent):
        """Тест свойства text_length."""
        assert sample_parsed_content.text_length == len(
            sample_parsed_content.text
        )

    def test_parsed_content_has_error_true(self, temp_dir: Path):
        """Тест свойства has_error когда error установлен."""
        content = ParsedContent(
            file_path=str(temp_dir / "test.html"),
            format="html",
            text="",
            metadata={},
            structure=[],
            semantic_blocks=[],
            quality={},
            file_metrics={},
            raw_data={},
            success=False,
            error="Test error",
        )

        assert content.has_error is True

    def test_parsed_content_has_error_false(self, sample_parsed_content: ParsedContent):
        """Тест свойства has_error когда нет ошибки."""
        assert sample_parsed_content.has_error is False

    def test_parsed_content_to_dict(self, sample_parsed_content: ParsedContent):
        """Тест конвертации ParsedContent в словарь."""
        result = sample_parsed_content.to_dict()

        assert "file_path" in result
        assert "format" in result
        assert "text_length" in result
        assert "metadata" in result
        assert "structure" in result
        assert "semantic_blocks" in result
        assert "quality" in result
        assert "file_metrics" in result
        assert "raw_data" in result
        assert "parsed_at" in result
        assert "success" in result
        assert "error" in result

    def test_parsed_content_to_dict_parsed_at_iso(self, sample_parsed_content: ParsedContent):
        """Тест что parsed_at форматируется как ISO строка."""
        result = sample_parsed_content.to_dict()

        assert isinstance(result["parsed_at"], str)
        assert "T" in result["parsed_at"]  # ISO формат содержит T разделитель

    def test_parsed_content_to_dict_includes_text_length(self, sample_parsed_content: ParsedContent):
        """Тест что text_length включён в вывод dict."""
        result = sample_parsed_content.to_dict()

        assert result["text_length"] == len(sample_parsed_content.text)

    def test_parsed_content_default_values(self, temp_dir: Path):
        """Тест значений по умолчанию для опциональных полей."""
        content = ParsedContent(
            file_path=str(temp_dir / "test.html"),
            format="html",
            text="test",
            success=True,
        )

        assert content.metadata == {}
        assert content.structure == []
        assert content.semantic_blocks == []
        assert content.quality == {}
        assert content.file_metrics == {}
        assert content.raw_data == {}
        assert content.error is None

    def test_parsed_content_parsed_at_auto(self, temp_dir: Path):
        """Тест что parsed_at автоматически устанавливается."""
        content = ParsedContent(
            file_path=str(temp_dir / "test.html"),
            format="html",
            text="test",
            success=True,
        )

        assert isinstance(content.parsed_at, datetime)

    def test_parsed_content_with_error_message(self, temp_dir: Path):
        """Тест создания ParsedContent с сообщением об ошибке."""
        content = ParsedContent(
            file_path=str(temp_dir / "test.html"),
            format="html",
            text="",
            metadata={},
            structure=[],
            semantic_blocks=[],
            quality={},
            file_metrics={},
            raw_data={},
            success=False,
            error="Parsing failed: file corrupted",
        )

        assert content.success is False
        assert content.error == "Parsing failed: file corrupted"
        assert content.has_error is True


class TestParsedContentEdgeCases:
    """Тесты граничных случаев для ParsedContent."""

    def test_parsed_content_empty_text(self, temp_dir: Path):
        """Тест ParsedContent с пустым текстом."""
        content = ParsedContent(
            file_path=str(temp_dir / "test.html"),
            format="html",
            text="",
            success=True,
        )

        assert content.text == ""
        assert content.text_length == 0

    def test_parsed_content_unicode_text(self, temp_dir: Path):
        """Тест ParsedContent с unicode текстом."""
        content = ParsedContent(
            file_path=str(temp_dir / "test.html"),
            format="html",
            text="Привет мир! 你好世界!",
            success=True,
        )

        # "Привет мир!" = 11 символов (включая пробел), " 你好世界!" = 6 символов = 17 всего
        assert content.text_length == 17

    def test_parsed_content_large_text(self, temp_dir: Path):
        """Тест ParsedContent с большим текстом."""
        large_text = "x" * 1_000_000

        content = ParsedContent(
            file_path=str(temp_dir / "test.html"),
            format="html",
            text=large_text,
            success=True,
        )

        assert content.text_length == 1_000_000

    def test_parsed_content_complex_metadata(self, temp_dir: Path):
        """Тест ParsedContent со сложными вложенными метаданными."""
        content = ParsedContent(
            file_path=str(temp_dir / "test.html"),
            format="html",
            text="test",
            metadata={
                "nested": {"key": "value"},
                "list": [1, 2, 3],
                "mixed": {"a": [1, 2], "b": {"c": "d"}},
            },
            success=True,
        )

        result = content.to_dict()
        assert result["metadata"]["nested"]["key"] == "value"
        assert result["metadata"]["list"] == [1, 2, 3]
