"""
Юнит-тесты для CLI (__init__.py).
"""

from unittest.mock import MagicMock, patch

from parser_manager import _build_cli_parser, _configure_logging, main
from parser_manager.models import (
    CorruptedFileError,
    DocumentNotFoundError,
    ParserError,
    ParsingFailedError,
    UnsupportedFormatError,
)


class TestBuildCliParser:
    """Тесты для _build_cli_parser."""

    def test_build_cli_parser_returns_argument_parser(self):
        """Тест что функция возвращает ArgumentParser."""
        parser = _build_cli_parser()
        assert parser is not None
        assert parser.prog == "parser-manager"

    def test_build_cli_parser_has_file_argument(self):
        """Тест что есть аргумент --file."""
        parser = _build_cli_parser()
        args = parser.parse_args(["--file", "test.html"])
        assert args.file == "test.html"

    def test_build_cli_parser_has_output_argument(self):
        """Тест что есть аргумент --output."""
        parser = _build_cli_parser()
        args = parser.parse_args(["--output", "result.json"])
        assert args.output == "result.json"

    def test_build_cli_parser_has_list_formats_argument(self):
        """Тест что есть аргумент --list-formats."""
        parser = _build_cli_parser()
        args = parser.parse_args(["--list-formats"])
        assert args.list_formats is True

    def test_build_cli_parser_has_pretty_argument(self):
        """Тест что есть аргумент --pretty."""
        parser = _build_cli_parser()
        args = parser.parse_args(["--pretty"])
        assert args.pretty is True

    def test_build_cli_parser_has_export_format_argument(self):
        """Тест что есть аргумент --export-format."""
        parser = _build_cli_parser()
        args = parser.parse_args(["--export-format", "md"])
        assert args.export_format == "md"

    def test_build_cli_parser_has_version_argument(self):
        """Тест что есть аргумент --version."""
        parser = _build_cli_parser()
        args = parser.parse_args(["--version"])
        assert args.version is True

    def test_build_cli_parser_has_verbose_argument(self):
        """Тест что есть аргумент --verbose."""
        parser = _build_cli_parser()
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True


class TestConfigureLogging:
    """Тесты для _configure_logging."""

    def test_configure_logging_verbose(self):
        """Тест настройки логирования с verbose=True."""
        _configure_logging(verbose=True)
        # Просто проверить что не падает

    def test_configure_logging_quiet(self):
        """Тест настройки логирования с verbose=False."""
        _configure_logging(verbose=False)
        # Просто проверить что не падает


class TestMainFunction:
    """Тесты для main функции."""

    def test_main_version_flag(self, capsys):
        """Тест флага --version."""
        result = main(["--version"])
        captured = capsys.readouterr()
        assert result == 0
        assert "Parser Manager v" in captured.out

    def test_main_list_formats_flag(self, capsys, mocker):
        """Тест флага --list-formats."""
        mocker.patch(
            "parser_manager.ParserFactory.get_available_formats", return_value=[".html", ".pdf"]
        )
        result = main(["--list-formats"])
        captured = capsys.readouterr()
        assert result == 0
        assert "Поддерживаемые форматы:" in captured.out

    def test_main_no_file_shows_help(self, capsys):
        """Тест что без --file показывается справка."""
        result = main([])
        assert result == 2

    def test_main_missing_file_returns_error(self, capsys):
        """Тест что отсутствующий файл возвращает ошибку."""
        result = main(["--file", "/nonexistent/file.html"])
        captured = capsys.readouterr()
        assert result == 1
        assert "Ошибка:" in captured.out

    def test_main_unsupported_format_returns_error(self, capsys, temp_dir):
        """Тест неподдерживаемого формата."""
        file_path = temp_dir / "test.xyz"
        file_path.write_text("test")
        result = main(["--file", str(file_path)])
        captured = capsys.readouterr()
        assert result == 1
        assert "Ошибка:" in captured.out

    def test_main_successful_parsing(self, capsys, sample_html_file, mocker):
        """Тест успешного парсинга."""
        # Mock export чтобы избежать проблем с модулем экспорта
        mock_result = MagicMock()
        mock_result.format = "html"
        mock_result.text_length = 100
        mock_result.export.return_value = '{"test": "result"}'
        mock_result.doc_stats = {"word_count": 50, "reading_time_min": 1}

        mock_parser = MagicMock()
        mock_parser.parse.return_value = mock_result

        mocker.patch("parser_manager.ParserFactory.create_parser", return_value=mock_parser)

        result = main(["--file", str(sample_html_file), "--export-format", "json"])

        assert result == 0
        assert mock_result.export.called

    def test_main_document_not_found_error(self, capsys):
        """Тест обработки DocumentNotFoundError."""
        with patch(
            "parser_manager.ParserFactory.create_parser",
            side_effect=DocumentNotFoundError("File not found"),
        ):
            result = main(["--file", "/nonexistent.html"])
            captured = capsys.readouterr()

        assert result == 1
        assert "Ошибка:" in captured.out

    def test_main_unsupported_format_error(self, capsys):
        """Тест обработки UnsupportedFormatError."""
        with patch(
            "parser_manager.ParserFactory.create_parser",
            side_effect=UnsupportedFormatError("Unsupported format"),
        ):
            result = main(["--file", "test.xyz"])
            captured = capsys.readouterr()

        assert result == 1
        assert "Ошибка:" in captured.out

    def test_main_parsing_failed_error(self, capsys):
        """Тест обработки ParsingFailedError."""
        with patch(
            "parser_manager.ParserFactory.create_parser",
            side_effect=ParsingFailedError("Parsing failed"),
        ):
            result = main(["--file", "test.html"])
            captured = capsys.readouterr()

        assert result == 1
        assert "Ошибка:" in captured.out

    def test_main_corrupted_file_error(self, capsys):
        """Тест обработки CorruptedFileError."""
        with patch(
            "parser_manager.ParserFactory.create_parser",
            side_effect=CorruptedFileError("File corrupted"),
        ):
            result = main(["--file", "test.html"])
            captured = capsys.readouterr()

        assert result == 1
        assert "Ошибка:" in captured.out

    def test_main_parser_error(self, capsys):
        """Тест обработки ParserError."""
        with patch(
            "parser_manager.ParserFactory.create_parser", side_effect=ParserError("Parser error")
        ):
            result = main(["--file", "test.html"])
            captured = capsys.readouterr()

        assert result == 1
        assert "Ошибка парсера:" in captured.out

    def test_main_generic_exception(self, capsys, mocker):
        """Тест обработки общего исключения."""
        mocker.patch(
            "parser_manager.ParserFactory.create_parser", side_effect=Exception("Unexpected error")
        )
        result = main(["--file", "test.html"])
        captured = capsys.readouterr()

        assert result == 1
        assert "Непредвиденная ошибка:" in captured.out

    def test_main_with_output_file(self, capsys, temp_dir, mocker):
        """Тест сохранения результата в файл."""
        output_file = temp_dir / "result.json"

        mock_result = MagicMock()
        mock_result.format = "html"
        mock_result.text_length = 100
        mock_result.export.return_value = '{"test": "result"}'
        mock_result.doc_stats = {"word_count": 50, "reading_time_min": 1}

        mock_parser = MagicMock()
        mock_parser.parse.return_value = mock_result

        mocker.patch("parser_manager.ParserFactory.create_parser", return_value=mock_parser)

        result = main(
            ["--file", "test.html", "--output", str(output_file), "--export-format", "json"]
        )
        captured = capsys.readouterr()

        assert result == 0
        assert output_file.exists()
        assert "OK: результат сохранён" in captured.out

    def test_main_with_pretty_json(self, capsys, mocker):
        """Тест красивого JSON вывода."""
        mock_result = MagicMock()
        mock_result.format = "html"
        mock_result.text_length = 100
        mock_result.export.return_value = '{\n  "test": "result"\n}'
        mock_result.doc_stats = {"word_count": 50, "reading_time_min": 1}

        mock_parser = MagicMock()
        mock_parser.parse.return_value = mock_result

        mocker.patch("parser_manager.ParserFactory.create_parser", return_value=mock_parser)

        result = main(["--file", "test.html", "--pretty", "--export-format", "json"])
        assert result == 0
        # Проверить что export был вызван
        assert mock_result.export.called

    def test_main_default_export_format_report(self, capsys, mocker):
        """Тест что по умолчанию используется report формат."""
        mock_result = MagicMock()
        mock_result.format = "html"
        mock_result.text_length = 100
        mock_result.export.return_value = "Report output"
        mock_result.doc_stats = {"word_count": 50, "reading_time_min": 1}

        mock_parser = MagicMock()
        mock_parser.parse.return_value = mock_result

        mocker.patch("parser_manager.ParserFactory.create_parser", return_value=mock_parser)

        result = main(["--file", "test.html"])
        assert result == 0
        # Должен вызвать export с форматом "report" по умолчанию
        mock_result.export.assert_called_with("report")
