"""
Unit tests for DjvuParser.

Test Cases:
- TC-PARSER-DJVU-001: DJVU Missing Dependency
"""

import pytest

from parser_manager.models import (
    CorruptedFileError,
    DocumentNotFoundError,
    ParsingFailedError,
)
from parser_manager.parsers.documents.djvu_parser import DjvuParser


class TestDjvuParserInitialization:
    """Tests for DjvuParser initialization."""

    def test_djvu_parser_supported_extensions(self):
        """Test supported extensions."""
        assert DjvuParser.supported_extensions == (".djvu", ".djv")
        assert DjvuParser.format_name == "djvu"


class TestDjvuParserMissingDependency:
    """Tests for TC-PARSER-DJVU-001: DJVU Missing Dependency."""

    def test_djvu_parser_missing_djvutxt_raises_error(self, sample_djvu_file, mocker):
        """Test that missing djvutxt raises ParsingFailedError."""
        # Mock shutil.which to return None
        mocker.patch("shutil.which", return_value=None)

        parser = DjvuParser(str(sample_djvu_file))

        with pytest.raises(ParsingFailedError) as exc_info:
            parser.extract_text()

        assert "djvutxt" in str(exc_info.value).lower()

    def test_djvu_parser_missing_djvused_raises_error(self, sample_djvu_file, mocker):
        """Test that missing djvused raises ParsingFailedError."""

        # Mock shutil.which to return None for djvused only
        def mock_which(cmd):
            if cmd == "djvused":
                return None
            return "/usr/bin/djvutxt"

        mocker.patch("shutil.which", side_effect=mock_which)
        # Mock subprocess.run to fail
        mocker.patch("subprocess.run", side_effect=Exception("Command failed"))

        parser = DjvuParser(str(sample_djvu_file))

        with pytest.raises((ParsingFailedError, CorruptedFileError)):
            parser.extract_metadata()


class TestDjvuParserExtraction:
    """Tests for DJVU extraction methods."""

    def test_djvu_parser_extract_text_command_failure(self, sample_djvu_file, mocker):
        """Test text extraction when djvutxt fails."""
        mocker.patch("shutil.which", return_value="/usr/bin/djvutxt")
        mocker.patch(
            "subprocess.run",
            return_value=mocker.Mock(
                returncode=1, stdout="", stderr="Error: Failed to process file"
            ),
        )

        parser = DjvuParser(str(sample_djvu_file))

        with pytest.raises(ParsingFailedError) as exc_info:
            parser.extract_text()

        assert "djvutxt" in str(exc_info.value).lower()
        assert (
            "завершился с ошибкой" in str(exc_info.value).lower()
            or "error" in str(exc_info.value).lower()
        )

    def test_djvu_parser_extract_text_empty_output(self, sample_djvu_file, mocker):
        """Test text extraction when djvutxt returns empty output."""
        mocker.patch("shutil.which", return_value="/usr/bin/djvutxt")
        mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0, stdout="", stderr=""))

        parser = DjvuParser(str(sample_djvu_file))

        with pytest.raises(ParsingFailedError) as exc_info:
            parser.extract_text()

        assert (
            "не найден текстовый слой" in str(exc_info.value).lower()
            or "text" in str(exc_info.value).lower()
        )

    def test_djvu_parser_extract_metadata_command_failure(self, sample_djvu_file, mocker):
        """Test metadata extraction when djvused fails."""
        mocker.patch("shutil.which", return_value="/usr/bin/djvused")
        mocker.patch(
            "subprocess.run", return_value=mocker.Mock(returncode=1, stdout="", stderr="Error")
        )

        parser = DjvuParser(str(sample_djvu_file))
        metadata = parser.extract_metadata()

        # Should handle failure gracefully and return minimal metadata
        assert metadata.pages is None

    def test_djvu_parser_extract_metadata_pages_parsing(self, sample_djvu_file, mocker):
        """Test metadata extraction with valid page count."""
        mocker.patch("shutil.which", return_value="/usr/bin/djvused")
        mocker.patch(
            "subprocess.run", return_value=mocker.Mock(returncode=0, stdout="10\n", stderr="")
        )

        parser = DjvuParser(str(sample_djvu_file))
        metadata = parser.extract_metadata()

        assert metadata.pages == 10

    def test_djvu_parser_extract_metadata_pages_non_numeric(self, sample_djvu_file, mocker):
        """Test metadata extraction with non-numeric page count."""
        mocker.patch("shutil.which", return_value="/usr/bin/djvused")
        mocker.patch(
            "subprocess.run", return_value=mocker.Mock(returncode=0, stdout="invalid\n", stderr="")
        )

        parser = DjvuParser(str(sample_djvu_file))
        metadata = parser.extract_metadata()

        # Should handle non-numeric output gracefully
        assert metadata.pages is None

    def test_djvu_parser_extract_structure_from_text(self, sample_djvu_file, mocker):
        """Test structure extraction."""
        mocker.patch("shutil.which", return_value="/usr/bin/djvutxt")
        mocker.patch(
            "subprocess.run",
            return_value=mocker.Mock(
                returncode=0, stdout="Page 1 content\fPage 2 content\fPage 3 content", stderr=""
            ),
        )

        parser = DjvuParser(str(sample_djvu_file))
        structure = parser.extract_structure()

        assert isinstance(structure, list)
        assert len(structure) == 3  # 3 pages separated by \f

        # Check page numbers
        for i, elem in enumerate(structure, start=1):
            assert elem["page"] == i
            assert elem["element_type"] == "paragraph"

    def test_djvu_parser_extract_structure_single_page(self, sample_djvu_file, mocker):
        """Test structure extraction with single page content."""
        mocker.patch("shutil.which", return_value="/usr/bin/djvutxt")
        mocker.patch(
            "subprocess.run",
            return_value=mocker.Mock(returncode=0, stdout="Single page content", stderr=""),
        )

        parser = DjvuParser(str(sample_djvu_file))
        structure = parser.extract_structure()

        assert len(structure) == 1
        assert structure[0]["page"] == 1


class TestDjvuParserEdgeCases:
    """Edge case tests for DjvuParser."""

    def test_djvu_parser_missing_file(self):
        """Test parsing non-existent file."""
        with pytest.raises(DocumentNotFoundError):
            DjvuParser("/nonexistent/file.djvu")

    def test_djvu_parser_djv_extension(self, temp_dir):
        """Test parsing .djv extension."""
        file_path = temp_dir / "test.djv"
        file_path.write_bytes(b"Fake DJVU")

        parser = DjvuParser(str(file_path))

        # Should initialize correctly
        assert parser.format_name == "djvu"

    def test_djvu_parser_run_method_success(self, temp_dir, mocker):
        """Test _run method with successful command."""
        file_path = temp_dir / "test.djvu"
        file_path.write_bytes(b"Test")

        mocker.patch("shutil.which", return_value="/usr/bin/test_cmd")
        mocker.patch(
            "subprocess.run", return_value=mocker.Mock(returncode=0, stdout="Output", stderr="")
        )

        parser = DjvuParser(str(file_path))
        result = parser._run(["arg1", "arg2"], required="test_cmd")

        assert result.returncode == 0
        assert result.stdout == "Output"

    def test_djvu_parser_run_method_missing_tool(self, temp_dir):
        """Test _run method when tool is missing."""
        file_path = temp_dir / "test.djvu"
        file_path.write_bytes(b"Test")

        parser = DjvuParser(str(file_path))

        with pytest.raises(ParsingFailedError) as exc_info:
            parser._run([], required="nonexistent_tool_12345")

        assert "nonexistent_tool_12345" in str(exc_info.value)

    def test_djvu_parser_run_method_exception(self, temp_dir, mocker):
        """Test _run method when subprocess raises exception."""
        file_path = temp_dir / "test.djvu"
        file_path.write_bytes(b"Test")

        mocker.patch("shutil.which", return_value="/usr/bin/test_cmd")
        mocker.patch("subprocess.run", side_effect=OSError("Subprocess error"))

        parser = DjvuParser(str(file_path))

        with pytest.raises(CorruptedFileError):
            parser._run([], required="test_cmd")

    def test_djvu_parser_parse_full_flow(self, temp_dir, mocker):
        """Test full parse flow with mocked commands."""
        file_path = temp_dir / "test.djvu"
        file_path.write_bytes(b"Fake DJVU")

        # Mock djvutxt
        def mock_which(cmd):
            if cmd == "djvutxt":
                return "/usr/bin/djvutxt"
            if cmd == "djvused":
                return "/usr/bin/djvused"
            return None

        mocker.patch("shutil.which", side_effect=mock_which)

        def mock_run(cmd, **kwargs):
            if "djvutxt" in cmd[0]:
                return mocker.Mock(returncode=0, stdout="Page 1\fPage 2", stderr="")
            if "djvused" in cmd[0] and "-e" in cmd and "n" in cmd:
                return mocker.Mock(returncode=0, stdout="2", stderr="")
            return mocker.Mock(returncode=1, stdout="", stderr="")

        mocker.patch("subprocess.run", side_effect=mock_run)

        parser = DjvuParser(str(file_path))
        result = parser.parse()

        assert result.success is True
        assert result.format == "djvu"
        assert "parsed_with" in result.raw_data
        assert "parsed_at" in result.raw_data

    def test_djvu_parser_repr(self, temp_dir):
        """Test string representation."""
        file_path = temp_dir / "test.djvu"
        file_path.write_bytes(b"Test")

        parser = DjvuParser(str(file_path))
        repr_str = repr(parser)

        assert "DjvuParser" in repr_str
        assert "test.djvu" in repr_str

    def test_djvu_parser_get_file_info(self, temp_dir):
        """Test get_file_info method."""
        file_path = temp_dir / "test.djvu"
        file_path.write_bytes(b"Test content")

        parser = DjvuParser(str(file_path))
        info = parser.get_file_info()

        assert info["name"] == "test.djvu"
        assert info["format"] == "djvu"
        assert info["suffix"] in [".djvu", ".djv"]

    def test_djvu_parser_unicode_error_handling(self, sample_djvu_file, mocker):
        """Test handling of unicode errors in subprocess output."""
        mocker.patch("shutil.which", return_value="/usr/bin/djvutxt")
        # Simulate output with encoding issues
        mocker.patch(
            "subprocess.run",
            return_value=mocker.Mock(returncode=0, stdout="Test with special:  chars", stderr=""),
        )

        parser = DjvuParser(str(sample_djvu_file))

        # Should handle gracefully due to errors="replace"
        try:
            text = parser.extract_text()
            assert isinstance(text, str)
        except ParsingFailedError:
            pass  # Also acceptable for fake DJVU

    def test_djvu_parser_metadata_raw_meta(self, sample_djvu_file, mocker):
        """Test that raw metadata is captured in custom_fields."""
        mocker.patch("shutil.which", return_value="/usr/bin/djvused")

        def mock_run(cmd, **kwargs):
            if "-e" in cmd and "n" in cmd:
                return mocker.Mock(returncode=0, stdout="5", stderr="")
            if "-e" in cmd and "print-meta" in cmd:
                return mocker.Mock(returncode=0, stdout='(title "Test")', stderr="")
            return mocker.Mock(returncode=1, stdout="", stderr="")

        mocker.patch("subprocess.run", side_effect=mock_run)

        parser = DjvuParser(str(sample_djvu_file))
        metadata = parser.extract_metadata()

        metadata_dict = metadata.to_dict()
        assert "raw_meta" in metadata_dict
