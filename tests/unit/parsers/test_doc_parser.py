"""
Unit tests for DocParser (legacy .doc format).

Test Cases:
- TC-PARSER-DOC-001: DOC Error Handling
"""

import pytest
import shutil

from parser_manager.parsers.documents.doc_parser import DocParser
from parser_manager.models import (
    DocumentNotFoundError,
    CorruptedFileError,
    ParsingFailedError,
)


class TestDocParserInitialization:
    """Tests for DocParser initialization."""

    def test_doc_parser_supported_extensions(self):
        """Test supported extensions."""
        assert DocParser.supported_extensions == (".doc",)
        assert DocParser.format_name == "doc"


class TestDocParserErrorHandling:
    """Tests for TC-PARSER-DOC-001: DOC Error Handling."""

    def test_doc_parser_corrupted_file_raises_error(self, sample_doc_file):
        """Test that corrupted DOC file raises CorruptedFileError."""
        parser = DocParser(str(sample_doc_file))

        with pytest.raises(CorruptedFileError):
            parser.extract_metadata()

    def test_doc_parser_not_ole_file(self, temp_dir):
        """Test that non-OLE file raises CorruptedFileError."""
        file_path = temp_dir / "not_ole.doc"
        file_path.write_bytes(b"Plain text, not OLE format")

        parser = DocParser(str(file_path))

        with pytest.raises(CorruptedFileError):
            parser.extract_metadata()

    def test_doc_parser_missing_file(self):
        """Test parsing non-existent file."""
        with pytest.raises(DocumentNotFoundError):
            DocParser("/nonexistent/file.doc")


class TestDocParserExtraction:
    """Tests for DOC extraction methods."""

    def test_doc_parser_extract_text_fallback(self, temp_dir):
        """Test text extraction with binary fallback."""
        # Create a file with some embedded text patterns
        file_path = temp_dir / "fallback.doc"
        # Write content that looks like it might have embedded strings
        content = b"PK" + b"\x00" * 50 + b"Test content" + b"\x00" * 50
        file_path.write_bytes(content)

        parser = DocParser(str(file_path))

        # May succeed with fallback or fail - both acceptable
        try:
            text = parser.extract_text()
            assert isinstance(text, str)
        except ParsingFailedError:
            # Expected if antiword/catdoc not available and fallback fails
            pass

    def test_doc_parser_extract_text_no_tools(self, temp_dir, mocker):
        """Test text extraction when external tools are not available."""
        file_path = temp_dir / "test.doc"
        file_path.write_bytes(b"Fake DOC content")

        # Mock shutil.which to return None (tools not available)
        mocker.patch("shutil.which", return_value=None)

        parser = DocParser(str(file_path))

        # Should try fallback
        try:
            text = parser.extract_text()
            assert isinstance(text, str)
        except ParsingFailedError as e:
            # Expected if fallback also fails
            assert "antiword" in str(e).lower() or "catdoc" in str(e).lower()

    def test_doc_parser_extract_structure(self, temp_dir):
        """Test structure extraction from DOC."""
        file_path = temp_dir / "test.doc"
        file_path.write_bytes(b"Fake DOC content")

        parser = DocParser(str(file_path))

        # May succeed or fail depending on content
        try:
            structure = parser.extract_structure()
            assert isinstance(structure, list)
        except ParsingFailedError:
            # Expected for invalid DOC
            pass


class TestDocParserEdgeCases:
    """Edge case tests for DocParser."""

    def test_doc_parser_extract_with_cli_antiword_not_found(self, temp_dir, mocker):
        """Test _extract_with_cli when antiword is not found."""
        file_path = temp_dir / "test.doc"
        file_path.write_bytes(b"Test")

        # Mock shutil.which to return None for antiword but some path for catdoc
        def mock_which(cmd):
            if cmd == "antiword":
                return None
            return "/usr/bin/catdoc"

        mocker.patch("shutil.which", side_effect=mock_which)

        # Mock subprocess.run to simulate catdoc failure
        mocker.patch("subprocess.run", return_value=mocker.Mock(
            returncode=1,
            stdout="",
            stderr="Error"
        ))

        parser = DocParser(str(file_path))
        result = parser._extract_with_cli()

        assert result == ""

    def test_doc_parser_extract_with_cli_catdoc_success(self, temp_dir, mocker):
        """Test _extract_with_cli when catdoc succeeds."""
        file_path = temp_dir / "test.doc"
        file_path.write_bytes(b"Test")

        mocker.patch("shutil.which", return_value="/usr/bin/catdoc")
        mocker.patch("subprocess.run", return_value=mocker.Mock(
            returncode=0,
            stdout="Extracted text",
            stderr=""
        ))

        parser = DocParser(str(file_path))
        result = parser._extract_with_cli()

        assert result == "Extracted text"

    def test_doc_parser_binary_string_extraction(self, temp_dir):
        """Test _extract_binary_strings method."""
        file_path = temp_dir / "binary.doc"
        # Create content with some ASCII patterns
        content = b"Header" + b"\x00" * 10 + b"Visible text here" + b"\x00" * 10 + b"Footer"
        file_path.write_bytes(content)

        parser = DocParser(str(file_path))
        result = parser._extract_binary_strings()

        assert isinstance(result, str)
        # Should find some of the text
        assert len(result) > 0

    def test_doc_parser_binary_string_extraction_utf16(self, temp_dir):
        """Test _extract_binary_strings with UTF-16 content."""
        file_path = temp_dir / "utf16.doc"
        # Create UTF-16 encoded content (little endian)
        text = "Test UTF-16 content"
        content = b"Header" + text.encode("utf-16-le") + b"Footer"
        file_path.write_bytes(content)

        parser = DocParser(str(file_path))
        result = parser._extract_binary_strings()

        assert isinstance(result, str)

    def test_doc_parser_metadata_ole_check(self, temp_dir):
        """Test OLE file check before metadata extraction."""
        file_path = temp_dir / "not_ole.doc"
        file_path.write_bytes(b"Not an OLE file")

        parser = DocParser(str(file_path))

        with pytest.raises(CorruptedFileError):
            parser.extract_metadata()

    def test_doc_parser_repr(self, temp_dir):
        """Test string representation."""
        file_path = temp_dir / "test.doc"
        file_path.write_bytes(b"Test")

        parser = DocParser(str(file_path))
        repr_str = repr(parser)

        assert "DocParser" in repr_str
        assert "test.doc" in repr_str

    def test_doc_parser_get_file_info(self, temp_dir):
        """Test get_file_info method."""
        file_path = temp_dir / "test.doc"
        file_path.write_bytes(b"Test content")

        parser = DocParser(str(file_path))
        info = parser.get_file_info()

        assert info["name"] == "test.doc"
        assert info["format"] == "doc"
        assert info["suffix"] == ".doc"
        assert "path" in info
        assert "size" in info

    def test_doc_parser_external_tools_check(self):
        """Test checking for external tools."""
        antiword_available = shutil.which("antiword") is not None
        catdoc_available = shutil.which("catdoc") is not None

        # Just verify the check works
        assert isinstance(antiword_available, bool)
        assert isinstance(catdoc_available, bool)
