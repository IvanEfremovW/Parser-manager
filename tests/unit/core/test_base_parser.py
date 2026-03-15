"""
Юнит-тесты для абстрактного класса BaseParser.

Тест-кейсы:
- TC-CORE-001: Инициализация BaseParser
- TC-CORE-002: BaseParser файл не найден
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from parser_manager.core.base_parser import BaseParser
from parser_manager.models import (
    DocumentNotFoundError,
    UnsupportedFormatError,
    ParserError,
    ParsedContent,
    DocumentMetadata,
)


class ConcreteParser(BaseParser):
    """Конкретная реализация BaseParser для тестирования."""

    supported_extensions = (".txt", ".test")
    format_name = "html"  # Используем поддерживаемый формат для тестов

    def parse(self) -> ParsedContent:
        return ParsedContent(
            file_path=str(self.file_path),
            format=self.format_name,
            text="test content",
            metadata={},
            structure=[],
            semantic_blocks=[],
            quality={},
            file_metrics={},
            raw_data={},
            success=True,
        )

    def extract_text(self) -> str:
        return "test text"

    def extract_metadata(self) -> DocumentMetadata:
        return DocumentMetadata()


class TestBaseParserInitialization:
    """Тесты для TC-CORE-001: Инициализация BaseParser."""

    def test_parser_init_with_valid_file(self, temp_dir: Path):
        """Тест инициализации парсера с валидным путём к файлу."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("test content")

        parser = ConcreteParser(str(file_path))

        assert parser.file_path == file_path
        assert parser.format_name == "html"  # Используем поддерживаемый формат для тестов
        assert parser.supported_extensions == (".txt", ".test")

    def test_parser_init_stores_options(self, temp_dir: Path):
        """Тест сохранения дополнительных опций."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("test content")

        parser = ConcreteParser(str(file_path), encoding="utf-8", strict=True)

        assert parser.options == {"encoding": "utf-8", "strict": True}

    def test_parser_repr(self, temp_dir: Path):
        """Тест строкового представления парсера."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("test content")

        parser = ConcreteParser(str(file_path))

        assert repr(parser) == "ConcreteParser(file='test.txt')"


class TestBaseParserFileValidation:
    """Тесты для TC-CORE-002: BaseParser файл не найден."""

    def test_parser_raises_on_missing_file(self):
        """Тест выброса DocumentNotFoundError для отсутствующего файла."""
        with pytest.raises(DocumentNotFoundError) as exc_info:
            ConcreteParser("/nonexistent/path/file.txt")

        assert "Файл не найден" in str(exc_info.value)

    def test_parser_raises_on_directory(self, temp_dir: Path):
        """Тест выброса ParserError когда путь является директорией."""
        with pytest.raises(ParserError) as exc_info:
            ConcreteParser(str(temp_dir))

        assert "не является файлом" in str(exc_info.value)

    def test_parser_raises_on_unsupported_extension(self, temp_dir: Path):
        """Тест выброса UnsupportedFormatError для неподдерживаемого расширения."""
        file_path = temp_dir / "test.unsupported"
        file_path.write_text("test content")

        with pytest.raises(UnsupportedFormatError) as exc_info:
            ConcreteParser(str(file_path))

        assert ".unsupported" in str(exc_info.value)
        assert "поддерживаются только" in str(exc_info.value)

    def test_parser_accepts_supported_extension(self, temp_dir: Path):
        """Тест принятия файлов с поддерживаемым расширением."""
        file_path = temp_dir / "test.test"
        file_path.write_text("test content")

        # Не должно выбрасывать исключение
        parser = ConcreteParser(str(file_path))
        assert parser is not None


class TestBaseParserMethods:
    """Тесты для служебных методов BaseParser."""

    @pytest.fixture
    def parser(self, temp_dir: Path) -> ConcreteParser:
        """Создать тестовый парсер."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("test content")
        return ConcreteParser(str(file_path))

    def test_get_file_info(self, parser: ConcreteParser):
        """Тест get_file_info возвращает корректную информацию."""
        info = parser.get_file_info()

        assert "path" in info
        assert "name" in info
        assert "size" in info
        assert "suffix" in info
        assert "format" in info

        assert info["name"] == "test.txt"
        assert info["suffix"] == ".txt"
        assert info["format"] == "html"  # Используем поддерживаемый формат для тестов

    def test_validate_parse_result_success(self, parser: ConcreteParser):
        """Тест валидации успешного результата парсинга."""
        result = parser.parse()

        assert parser.validate_parse_result(result) is True

    def test_validate_parse_result_wrong_type(self, parser: ConcreteParser):
        """Тест провала валидации для неверного типа результата."""
        assert parser.validate_parse_result("not a ParsedContent") is False

    def test_validate_parse_result_wrong_format(self, parser: ConcreteParser, temp_dir: Path):
        """Тест провала валидации для неверного формата."""
        # Создать ParsedContent с другим поддерживаемым форматом
        result = ParsedContent(
            file_path=str(temp_dir / "test.html"),
            format="pdf",  # Отличается от format_name парсера который равен "html"
            text="test",
            metadata={},
            structure=[],
            semantic_blocks=[],
            quality={},
            file_metrics={},
            raw_data={},
            success=True,
        )

        assert parser.validate_parse_result(result) is False

    def test_validate_parse_result_failed_without_error(self, parser: ConcreteParser):
        """Тест провала валидации когда success=False но error=None."""
        # Этот тест проверяет логику валидации, но мы не можем создать невалидный ParsedContent
        # напрямую из-за валидации __post_init__. Вместо этого создаём валидный объект
        # и вручную изменяем его для симуляции условия.
        result = parser.parse()
        result.success = False
        result.error = None  # Это должно провалить валидацию

        assert parser.validate_parse_result(result) is False

    def test_extract_structure_default_implementation(self, parser: ConcreteParser):
        """Тест что extract_structure возвращает пустой список по умолчанию."""
        assert parser.extract_structure() == []


class TestBaseParserEdgeCases:
    """Тесты граничных случаев для BaseParser."""

    def test_parser_with_unicode_path(self, temp_dir: Path):
        """Тест парсера с unicode символами в пути."""
        file_path = temp_dir / "тест.txt"
        file_path.write_text("тестовое содержимое", encoding="utf-8")

        parser = ConcreteParser(str(file_path))
        assert parser.file_path.name == "тест.txt"

    def test_parser_with_spaces_in_path(self, temp_dir: Path):
        """Тест парсера с пробелами в пути к файлу."""
        file_path = temp_dir / "test file.txt"
        file_path.write_text("test content")

        parser = ConcreteParser(str(file_path))
        assert parser.file_path == file_path

    def test_parser_case_insensitive_extension(self, temp_dir: Path):
        """Тест что сравнение расширений регистронезависимое."""
        file_path = temp_dir / "test.TXT"
        file_path.write_text("test content")

        parser = ConcreteParser(str(file_path))
        assert parser is not None
