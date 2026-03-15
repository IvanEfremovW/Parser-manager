"""
Unit tests for parsing service.
"""

from pathlib import Path

import pytest

from parser_manager.api.service import parse_file_sync, save_upload_to_temp
from parser_manager.models import DocumentNotFoundError, UnsupportedFormatError


class TestParseFileSync:
    """Tests for parse_file_sync function."""

    def test_parse_file_sync_html(self, sample_html_file):
        """Test parsing HTML file."""
        result = parse_file_sync(str(sample_html_file))

        assert isinstance(result, dict)
        assert result["format"] == "html"
        assert result["success"] is True
        assert "text_length" in result  # to_dict() returns text_length, not text
        assert "metadata" in result
        assert "structure" in result

    def test_parse_file_sync_pdf(self, sample_pdf_file):
        """Test parsing PDF file."""
        result = parse_file_sync(str(sample_pdf_file))

        assert isinstance(result, dict)
        assert result["format"] == "pdf"
        assert result["success"] is True

    def test_parse_file_sync_docx(self, sample_docx_file):
        """Test parsing DOCX file."""
        result = parse_file_sync(str(sample_docx_file))

        assert isinstance(result, dict)
        assert result["format"] == "docx"
        assert result["success"] is True

    def test_parse_file_sync_returns_dict(self, sample_html_file):
        """Test that result is a dictionary."""
        result = parse_file_sync(str(sample_html_file))

        assert isinstance(result, dict)

    def test_parse_file_sync_has_required_fields(self, sample_html_file):
        """Test that result has all required fields."""
        result = parse_file_sync(str(sample_html_file))

        required_fields = [
            "file_path",
            "format",
            "text_length",  # to_dict() returns text_length, not text
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
        """Test parsing non-existent file."""

        with pytest.raises(DocumentNotFoundError):
            parse_file_sync("/nonexistent/file.html")

    def test_parse_file_sync_unsupported_format(self, temp_dir):
        """Test parsing unsupported format."""
        file_path = temp_dir / "test.xyz"
        file_path.write_text("test content")

        with pytest.raises(UnsupportedFormatError):
            parse_file_sync(str(file_path))


class TestSaveUploadToTemp:
    """Tests for save_upload_to_temp function."""

    def test_save_upload_to_temp_creates_file(self):
        """Test that function creates a temp file."""
        content = b"Test content"
        result = save_upload_to_temp(content, ".html")

        assert isinstance(result, Path)
        assert result.exists()
        assert result.read_bytes() == content

    def test_save_upload_to_temp_correct_suffix(self):
        """Test that file has correct suffix."""
        content = b"Test content"
        result = save_upload_to_temp(content, ".pdf")

        assert result.suffix == ".pdf"

    def test_save_upload_to_temp_default_suffix(self):
        """Test default suffix when not provided."""
        content = b"Test content"
        result = save_upload_to_temp(content, suffix=None)

        assert result.suffix == ".bin"

    def test_save_upload_to_temp_in_correct_dir(self):
        """Test that file is created in correct directory."""
        content = b"Test content"
        result = save_upload_to_temp(content, ".html")

        assert "parser_manager_uploads" in str(result)
        assert result.parent.exists()

    def test_save_upload_to_temp_unique_names(self):
        """Test that multiple calls create unique files."""
        content = b"Test content"

        result1 = save_upload_to_temp(content, ".html")
        result2 = save_upload_to_temp(content, ".html")

        assert result1 != result2
        assert result1.name != result2.name

    def test_save_upload_to_temp_preserves_content(self):
        """Test that file content is preserved."""
        content = b"\x00\x01\x02\x03" * 1000
        result = save_upload_to_temp(content, ".bin")

        assert result.read_bytes() == content

    def test_save_upload_to_temp_large_file(self):
        """Test saving large file."""
        content = b"x" * 10_000_000  # 10 MB
        result = save_upload_to_temp(content, ".bin")

        assert result.exists()
        assert result.stat().st_size == 10_000_000

    def test_save_upload_to_temp_empty_content(self):
        """Test saving empty content."""
        content = b""
        result = save_upload_to_temp(content, ".html")

        assert result.exists()
        assert result.stat().st_size == 0

    def test_save_upload_to_temp_unicode_content(self):
        """Test saving unicode content."""
        content = "Привет мир! 你好世界!".encode()
        result = save_upload_to_temp(content, ".html")

        assert result.read_bytes() == content

    def test_save_upload_to_temp_cleanup(self):
        """Test that temp files can be cleaned up."""
        content = b"Test content"
        result = save_upload_to_temp(content, ".html")

        # Verify file exists
        assert result.exists()

        # Clean up
        result.unlink()

        assert not result.exists()


class TestSaveUploadToTempEdgeCases:
    """Edge case tests for save_upload_to_temp."""

    def test_save_upload_to_temp_special_characters_in_suffix(self):
        """Test with special characters in suffix."""
        content = b"Test"
        result = save_upload_to_temp(content, ".tar.gz")

        # Should handle the suffix
        assert result.suffix == ".gz"

    def test_save_upload_to_temp_no_leading_dot(self):
        """Test suffix without leading dot."""
        content = b"Test"
        result = save_upload_to_temp(content, "html")

        # tempfile.NamedTemporaryFile handles this
        assert result.exists()

    def test_save_upload_to_temp_concurrent_calls(self):
        """Test concurrent calls to save_upload_to_temp."""
        import threading

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
        # All paths should be unique
        assert len({str(r) for r in results}) == 10

    def test_save_upload_to_temp_directory_permissions(self):
        """Test that temp directory has correct permissions."""
        content = b"Test"
        result = save_upload_to_temp(content, ".html")

        # Should be able to read and write
        assert result.read_bytes() == content
        result.write_bytes(b"modified")
        assert result.read_bytes() == b"modified"
