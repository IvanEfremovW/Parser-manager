"""
Юнит-тесты для ParserFactory.

Тест-кейсы:
- TC-CORE-003: Регистрация ParserFactory
- TC-CORE-004: ParserFactory неподдерживаемый формат
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from parser_manager.core.parser_factory import ParserFactory
from parser_manager.models import UnsupportedFormatError


class MockParser:
    """Мок парсера для тестирования."""

    supported_extensions = (".mock",)
    format_name = "mock"

    def __init__(self, file_path: str, **kwargs):
        self.file_path = Path(file_path)
        self.options = kwargs


class TestParserFactoryRegistration:
    """Тесты для TC-CORE-003: Регистрация ParserFactory."""

    @pytest.fixture(autouse=True)
    def setup(self, clean_parser_registry):
        """Обеспечить чистый реестр для каждого теста."""
        self.registry = clean_parser_registry
        yield

    def test_register_single_parser(self):
        """Тест регистрации одного парсера."""
        self.registry.register_parser(".test", MockParser)

        assert ".test" in self.registry._parsers_registry
        assert self.registry._parsers_registry[".test"] == MockParser

    def test_register_parser_normalizes_extension(self):
        """Тест нормализации расширения с ведущей точкой."""
        self.registry.register_parser("test", MockParser)

        assert ".test" in self.registry._parsers_registry
        assert "test" not in self.registry._parsers_registry

    def test_register_parser_case_insensitive(self):
        """Тест что регистрация расширения регистронезависимая."""
        self.registry.register_parser(".TEST", MockParser)

        assert ".test" in self.registry._parsers_registry

    def test_register_multiple_parsers(self):
        """Тест массовой регистрации парсеров."""
        parsers = {
            ".ext1": MockParser,
            ".ext2": MockParser,
            ".ext3": MockParser,
        }

        self.registry.register_parsers(parsers)

        assert ".ext1" in self.registry._parsers_registry
        assert ".ext2" in self.registry._parsers_registry
        assert ".ext3" in self.registry._parsers_registry

    def test_register_parser_overwrites_existing(self):
        """Тест что регистрация того же расширения перезаписывает предыдущее."""
        class AnotherParser:
            supported_extensions = (".test",)
            format_name = "another"

        self.registry.register_parser(".test", MockParser)
        self.registry.register_parser(".test", AnotherParser)

        assert self.registry._parsers_registry[".test"] == AnotherParser

    def test_get_available_formats(self):
        """Тест получения списка доступных форматов."""
        self.registry.register_parser(".a", MockParser)
        self.registry.register_parser(".b", MockParser)
        self.registry.register_parser(".c", MockParser)

        formats = self.registry.get_available_formats()

        assert formats == [".a", ".b", ".c"]
        assert isinstance(formats, list)

    def test_get_available_formats_empty(self):
        """Тест получения форматов когда реестр пуст."""
        formats = self.registry.get_available_formats()

        assert formats == []

    def test_clear_registry(self):
        """Тест очистки реестра парсеров."""
        self.registry.register_parser(".test", MockParser)
        self.registry.clear_registry()

        assert len(self.registry._parsers_registry) == 0

    def test_is_format_supported_true(self, temp_dir: Path):
        """Тест проверки поддержки формата возвращает True для поддерживаемого формата."""
        self.registry.register_parser(".test", MockParser)

        file_path = temp_dir / "file.test"
        file_path.touch()

        assert self.registry.is_format_supported(str(file_path)) is True

    def test_is_format_supported_false(self, temp_dir: Path):
        """Тест проверки поддержки формата возвращает False для неподдерживаемого формата."""
        self.registry.register_parser(".test", MockParser)

        file_path = temp_dir / "file.unsupported"
        file_path.touch()

        assert self.registry.is_format_supported(str(file_path)) is False


class TestParserFactoryCreation:
    """Тесты для создания парсеров."""

    @pytest.fixture(autouse=True)
    def setup(self, clean_parser_registry):
        """Обеспечить чистый реестр для каждого теста."""
        self.registry = clean_parser_registry
        yield

    def test_create_parser_auto_detect(self, temp_dir: Path):
        """Тест создания парсера с авто-определением."""
        self.registry.register_parser(".test", MockParser)

        file_path = temp_dir / "file.test"
        file_path.write_text("test")

        parser = self.registry.create_parser(str(file_path))

        assert isinstance(parser, MockParser)
        assert parser.file_path == file_path

    def test_create_parser_explicit_class(self, temp_dir: Path):
        """Тест создания парсера с явным указанием класса."""
        file_path = temp_dir / "file.any"
        file_path.write_text("test")

        parser = self.registry.create_parser(str(file_path), parser_class=MockParser)

        assert isinstance(parser, MockParser)

    def test_create_parser_passes_kwargs(self, temp_dir: Path):
        """Тест передачи kwargs в парсер."""
        self.registry.register_parser(".test", MockParser)

        file_path = temp_dir / "file.test"
        file_path.write_text("test")

        parser = self.registry.create_parser(str(file_path), option1="value1", option2=42)

        assert parser.options == {"option1": "value1", "option2": 42}

    def test_create_parser_unsupported_format(self, temp_dir: Path):
        """Тест TC-CORE-004: UnsupportedFormatError для неизвестного формата."""
        self.registry.register_parser(".test", MockParser)

        file_path = temp_dir / "file.unknown"
        file_path.write_text("test")

        with pytest.raises(UnsupportedFormatError) as exc_info:
            self.registry.create_parser(str(file_path))

        assert ".unknown" in str(exc_info.value)
        assert ".test" in str(exc_info.value)

    def test_create_parser_case_insensitive_extension(self, temp_dir: Path):
        """Тест что сравнение расширений регистронезависимое."""
        self.registry.register_parser(".test", MockParser)

        file_path = temp_dir / "file.TEST"
        file_path.write_text("test")

        parser = self.registry.create_parser(str(file_path))

        assert isinstance(parser, MockParser)


class TestParserFactoryEdgeCases:
    """Тесты граничных случаев для ParserFactory."""

    @pytest.fixture(autouse=True)
    def setup(self, clean_parser_registry):
        """Обеспечить чистый реестр для каждого теста."""
        self.registry = clean_parser_registry
        yield

    def test_registry_thread_safety(self):
        """Тест базовой потокобезопасности операций реестра (операции dict)."""
        import threading

        errors = []

        def register():
            try:
                self.registry.register_parser(f".test_{threading.current_thread().name}", MockParser)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(self.registry._parsers_registry) == 5

    def test_register_parser_with_complex_extension(self):
        """Тест регистрации парсера со сложным расширением."""
        self.registry.register_parser(".tar.gz", MockParser)

        assert ".tar.gz" in self.registry._parsers_registry

    def test_create_parser_with_path_object(self, temp_dir: Path):
        """Тест создания парсера с объектом Path конвертированным в строку."""
        self.registry.register_parser(".test", MockParser)

        file_path = temp_dir / "file.test"
        file_path.write_text("test")

        # Path конвертируется в строку внутри
        parser = self.registry.create_parser(str(file_path))

        assert isinstance(parser, MockParser)

    def test_multiple_extensions_same_parser(self, temp_dir: Path):
        """Тест регистрации одного парсера для нескольких расширений."""
        self.registry.register_parser(".htm", MockParser)
        self.registry.register_parser(".html", MockParser)

        assert self.registry._parsers_registry[".htm"] == MockParser
        assert self.registry._parsers_registry[".html"] == MockParser
