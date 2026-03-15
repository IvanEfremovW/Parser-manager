"""
Юнит-тесты для пользовательских исключений.
"""

import pytest

from parser_manager.models.exceptions import (
    ParserError,
    UnsupportedFormatError,
    DocumentNotFoundError,
    ParsingFailedError,
    CorruptedFileError,
    InvalidConfigurationError,
)


class TestParserError:
    """Тесты для базового исключения ParserError."""

    def test_parser_error_basic(self):
        """Тест базового создания ParserError."""
        error = ParserError("Test error message")
        assert str(error) == "Test error message"

    def test_parser_error_inheritance(self):
        """Тест что ParserError наследуется от Exception."""
        error = ParserError("Test")
        assert isinstance(error, Exception)

    def test_parser_error_raise_catch(self):
        """Тест выброса и перехвата ParserError."""
        with pytest.raises(ParserError) as exc_info:
            raise ParserError("Something went wrong")

        assert "Something went wrong" in str(exc_info.value)


class TestUnsupportedFormatError:
    """Тесты для исключения UnsupportedFormatError."""

    def test_unsupported_format_error_basic(self):
        """Тест базового создания UnsupportedFormatError."""
        error = UnsupportedFormatError(".xyz format not supported")
        assert str(error) == ".xyz format not supported"

    def test_unsupported_format_error_inheritance(self):
        """Тест что UnsupportedFormatError наследуется от ParserError."""
        error = UnsupportedFormatError("Test")
        assert isinstance(error, ParserError)

    def test_unsupported_format_error_detailed(self):
        """Тест UnsupportedFormatError с детальным сообщением."""
        error = UnsupportedFormatError(
            "Формат файла '.xyz' не поддерживается. Доступные форматы: .html, .pdf"
        )
        assert ".xyz" in str(error)
        assert ".html" in str(error)


class TestDocumentNotFoundError:
    """Тесты для исключения DocumentNotFoundError."""

    def test_document_not_found_error_basic(self):
        """Тест базового создания DocumentNotFoundError."""
        error = DocumentNotFoundError("File not found: /path/to/file")
        assert str(error) == "File not found: /path/to/file"

    def test_document_not_found_error_inheritance(self):
        """Тест что DocumentNotFoundError наследуется от ParserError."""
        error = DocumentNotFoundError("Test")
        assert isinstance(error, ParserError)


class TestParsingFailedError:
    """Тесты для исключения ParsingFailedError."""

    def test_parsing_failed_error_basic(self):
        """Тест базового создания ParsingFailedError."""
        error = ParsingFailedError("Failed to parse document")
        assert str(error) == "Failed to parse document"

    def test_parsing_failed_error_inheritance(self):
        """Тест что ParsingFailedError наследуется от ParserError."""
        error = ParsingFailedError("Test")
        assert isinstance(error, ParserError)

    def test_parsing_failed_error_with_cause(self):
        """Тест ParsingFailedError с первопричиной."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            error = ParsingFailedError(f"Parsing failed: {e}")
            assert "Original error" in str(error)


class TestCorruptedFileError:
    """Тесты для исключения CorruptedFileError."""

    def test_corrupted_file_error_basic(self):
        """Тест базового создания CorruptedFileError."""
        error = CorruptedFileError("File is corrupted")
        assert str(error) == "File is corrupted"

    def test_corrupted_file_error_inheritance(self):
        """Тест что CorruptedFileError наследуется от ParserError."""
        error = CorruptedFileError("Test")
        assert isinstance(error, ParserError)


class TestInvalidConfigurationError:
    """Тесты для исключения InvalidConfigurationError."""

    def test_invalid_configuration_error_basic(self):
        """Тест базового создания InvalidConfigurationError."""
        error = InvalidConfigurationError("Invalid parser configuration")
        assert str(error) == "Invalid parser configuration"

    def test_invalid_configuration_error_inheritance(self):
        """Тест что InvalidConfigurationError наследуется от ParserError."""
        error = InvalidConfigurationError("Test")
        assert isinstance(error, ParserError)


class TestExceptionHierarchy:
    """Тесты для иерархии исключений."""

    def test_all_exceptions_are_parser_errors(self):
        """Тест что все пользовательские исключения наследуются от ParserError."""
        exceptions = [
            UnsupportedFormatError("test"),
            DocumentNotFoundError("test"),
            ParsingFailedError("test"),
            CorruptedFileError("test"),
            InvalidConfigurationError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, ParserError)

    def test_catch_all_with_base_exception(self):
        """Тест что все исключения могут быть перехвачены с ParserError."""
        exceptions_to_raise = [
            UnsupportedFormatError,
            DocumentNotFoundError,
            ParsingFailedError,
            CorruptedFileError,
            InvalidConfigurationError,
        ]

        for exc_class in exceptions_to_raise:
            with pytest.raises(ParserError):
                raise exc_class("Test error")

    def test_specific_exception_can_be_caught(self):
        """Тест что специфичные исключения могут быть перехвачены индивидуально."""
        with pytest.raises(UnsupportedFormatError):
            raise UnsupportedFormatError("Specific error")

        with pytest.raises(DocumentNotFoundError):
            raise DocumentNotFoundError("Specific error")
