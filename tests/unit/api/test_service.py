"""
Юнит-тесты для сервиса парсинга.
"""

import json
import threading
from pathlib import Path

import pytest

from parser_manager.api.service import export_file_sync, parse_file_sync, save_upload_to_temp
from parser_manager.models import DocumentNotFoundError, UnsupportedFormatError


class TestParseFileSync:
    """Тесты для функции parse_file_sync."""

    def test_parse_file_sync_html(self, sample_html_file):
        """Тест парсинга HTML файла."""
        result = parse_file_sync(str(sample_html_file))

        assert isinstance(result, dict)
        assert result["format"] == "html"
        assert result["success"] is True
        assert "text_length" in result  # to_dict() возвращает text_length, а не text
        assert "metadata" in result
        assert "structure" in result

    def test_parse_file_sync_pdf(self, sample_pdf_file):
        """Тест парсинга PDF файла."""
        result = parse_file_sync(str(sample_pdf_file))

        assert isinstance(result, dict)
        assert result["format"] == "pdf"
        assert result["success"] is True

    def test_parse_file_sync_docx(self, sample_docx_file):
        """Тест парсинга DOCX файла."""
        result = parse_file_sync(str(sample_docx_file))

        assert isinstance(result, dict)
        assert result["format"] == "docx"
        assert result["success"] is True

    def test_parse_file_sync_returns_dict(self, sample_html_file):
        """Тест что результат возвращается как словарь."""
        result = parse_file_sync(str(sample_html_file))

        assert isinstance(result, dict)

    def test_parse_file_sync_has_required_fields(self, sample_html_file):
        """Тест что результат содержит все обязательные поля."""
        result = parse_file_sync(str(sample_html_file))

        required_fields = [
            "file_path",
            "format",
            "text_length",  # to_dict() возвращает text_length, а не text
            "metadata",
            "structure",
            "semantic_blocks",
            "quality",
            "file_metrics",
            "raw_data",
            "parsed_at",
            "success",
            "error",
        ]

        for field in required_fields:
            assert field in result

    def test_parse_file_sync_missing_file(self):
        """Тест парсинга несуществующего файла."""
        with pytest.raises(DocumentNotFoundError):
            parse_file_sync("/nonexistent/file.html")

    def test_parse_file_sync_unsupported_format(self, temp_dir):
        """Тест парсинга неподдерживаемого формата."""
        file_path = temp_dir / "test.xyz"
        file_path.write_text("test content")

        with pytest.raises(UnsupportedFormatError):
            parse_file_sync(str(file_path))


class TestSaveUploadToTemp:
    """Тесты для функции save_upload_to_temp."""

    def test_save_upload_to_temp_creates_file(self):
        """Тест что функция создаёт временный файл."""
        content = b"Test content"
        result = save_upload_to_temp(content, ".html")

        assert isinstance(result, Path)
        assert result.exists()
        assert result.read_bytes() == content

    def test_save_upload_to_temp_correct_suffix(self):
        """Тест что файл имеет правильный суффикс."""
        content = b"Test content"
        result = save_upload_to_temp(content, ".pdf")

        assert result.suffix == ".pdf"

    def test_save_upload_to_temp_default_suffix(self):
        """Тест суффикса по умолчанию когда не указан."""
        content = b"Test content"
        result = save_upload_to_temp(content, suffix=None)

        assert result.suffix == ".bin"

    def test_save_upload_to_temp_in_correct_dir(self):
        """Тест что файл создан в правильной директории."""
        content = b"Test content"
        result = save_upload_to_temp(content, ".html")

        assert "parser_manager_uploads" in str(result)
        assert result.parent.exists()

    def test_save_upload_to_temp_unique_names(self):
        """Тест что множественные вызовы создают уникальные файлы."""
        content = b"Test content"

        result1 = save_upload_to_temp(content, ".html")
        result2 = save_upload_to_temp(content, ".html")

        assert result1 != result2
        assert result1.name != result2.name

    def test_save_upload_to_temp_preserves_content(self):
        """Тест что содержимое файла сохраняется."""
        content = b"\x00\x01\x02\x03" * 1000
        result = save_upload_to_temp(content, ".bin")

        assert result.read_bytes() == content

    def test_save_upload_to_temp_large_file(self):
        """Тест сохранения большого файла."""
        content = b"x" * 10_000_000  # 10 MB
        result = save_upload_to_temp(content, ".bin")

        assert result.exists()
        assert result.stat().st_size == 10_000_000

    def test_save_upload_to_temp_empty_content(self):
        """Тест сохранения пустого содержимого."""
        content = b""
        result = save_upload_to_temp(content, ".html")

        assert result.exists()
        assert result.stat().st_size == 0

    def test_save_upload_to_temp_unicode_content(self):
        """Тест сохранения unicode содержимого."""
        content = "Привет мир! 你好世界!".encode()
        result = save_upload_to_temp(content, ".html")

        assert result.read_bytes() == content

    def test_save_upload_to_temp_cleanup(self):
        """Тест что временные файлы могут быть очищены."""
        content = b"Test content"
        result = save_upload_to_temp(content, ".html")

        # Проверить что файл существует
        assert result.exists()

        # Очистить
        result.unlink()

        assert not result.exists()

    def test_save_upload_to_temp_special_characters_in_suffix(self):
        """Тест со спецсимволами в суффиксе."""
        content = b"Test"
        result = save_upload_to_temp(content, ".tar.gz")

        # Должен обработать суффикс
        assert result.suffix == ".gz"

    def test_save_upload_to_temp_no_leading_dot(self):
        """Тест суффикса без ведущей точки."""
        content = b"Test"
        result = save_upload_to_temp(content, "html")

        # tempfile.NamedTemporaryFile обрабатывает это
        assert result.exists()

    def test_save_upload_to_temp_concurrent_calls(self):
        """Тест параллельных вызовов save_upload_to_temp."""
        results = []
        errors = []

        def save():
            try:
                result = save_upload_to_temp(b"test", ".html")
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=save) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10
        # Все пути должны быть уникальны
        assert len({str(r) for r in results}) == 10

    def test_save_upload_to_temp_directory_permissions(self):
        """Тест что временная директория имеет правильные права."""
        content = b"Test"
        result = save_upload_to_temp(content, ".html")

        # Должно быть возможно читать и писать
        assert result.read_bytes() == content
        result.write_bytes(b"modified")
        assert result.read_bytes() == b"modified"


class TestExportFileSync:
    """Тесты для функции export_file_sync."""

    def test_export_file_sync_json(self):
        """Тест экспорта в формат JSON."""
        result_dict = {
            "file_path": "/test/file.html",
            "format": "html",
            "text": "",
            "semantic_blocks": [],
            "doc_stats": {},
            "ast": {},
            "metadata": {},
            "quality": {},
            "file_metrics": {},
            "success": True,
            "error": None,
        }

        result = export_file_sync(result_dict, "json")

        assert isinstance(result, str)
        # Должен быть валидный JSON
        parsed = json.loads(result)
        assert parsed["format"] == "html"

    def test_export_file_sync_md(self):
        """Тест экспорта в формат Markdown."""
        result_dict = {
            "file_path": "/test/file.html",
            "format": "html",
            "text": "",
            "semantic_blocks": [],
            "doc_stats": {},
            "ast": {},
            "metadata": {},
            "quality": {},
            "file_metrics": {},
            "success": True,
            "error": None,
        }

        result = export_file_sync(result_dict, "md")

        assert isinstance(result, str)

    def test_export_file_sync_report(self):
        """Тест экспорта в формат отчёта."""
        result_dict = {
            "file_path": "/test/file.html",
            "format": "html",
            "text": "",
            "semantic_blocks": [],
            "doc_stats": {},
            "ast": {},
            "metadata": {},
            "quality": {},
            "file_metrics": {},
            "success": True,
            "error": None,
        }

        result = export_file_sync(result_dict, "report")

        assert isinstance(result, str)
