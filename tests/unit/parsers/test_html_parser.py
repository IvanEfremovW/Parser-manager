"""
Unit tests for HtmlParser.

Test Cases:
- TC-PARSER-HTML-001: HTML Parsing
"""

import pytest

from parser_manager.models import (
    DocumentNotFoundError,
    ParsedContent,
)
from parser_manager.parsers.html_parser import HtmlParser


class TestHtmlParserInitialization:
    """Tests for HtmlParser initialization."""

    def test_html_parser_supported_extensions(self):
        """Test supported extensions."""
        assert HtmlParser.supported_extensions == (".html", ".htm")
        assert HtmlParser.format_name == "html"


class TestHtmlParserParsing:
    """Tests for TC-PARSER-HTML-001: HTML Parsing."""

    def test_html_parser_parse_success(self, sample_html_file):
        """Test successful HTML parsing."""
        parser = HtmlParser(str(sample_html_file))
        result = parser.parse()

        assert isinstance(result, ParsedContent)
        assert result.success is True
        assert result.format == "html"
        assert result.error is None

    def test_html_parser_extract_text(self, sample_html_file):
        """Test text extraction from HTML."""
        parser = HtmlParser(str(sample_html_file))
        text = parser.extract_text()

        assert isinstance(text, str)
        assert "Main Heading" in text
        assert "test paragraph" in text.lower()
        # Script and style should be removed
        assert "console.log" not in text
        assert ".hidden" not in text

    def test_html_parser_extract_metadata(self, sample_html_file):
        """Test metadata extraction from HTML."""
        parser = HtmlParser(str(sample_html_file))
        metadata = parser.extract_metadata()

        assert metadata.title == "Test Document Title"
        assert metadata.author == "Test Author"
        assert metadata.language == "ru"

    def test_html_parser_extract_structure(self, sample_html_file):
        """Test structure extraction from HTML."""
        parser = HtmlParser(str(sample_html_file))
        structure = parser.extract_structure()

        assert len(structure) > 0

        # Check for different element types
        element_types = [elem["element_type"] for elem in structure]

        assert "heading" in element_types
        assert "paragraph" in element_types
        assert "list" in element_types
        assert "table" in element_types
        assert "link" in element_types

    def test_html_parser_heading_levels(self, sample_html_file):
        """Test that heading levels are correctly extracted."""
        parser = HtmlParser(str(sample_html_file))
        structure = parser.extract_structure()

        headings = [e for e in structure if e["element_type"] == "heading"]

        h1 = [h for h in headings if h["level"] == 1]
        h2 = [h for h in headings if h["level"] == 2]

        assert len(h1) >= 1
        assert len(h2) >= 1
        assert h1[0]["content"] == "Main Heading"

    def test_html_parser_link_metadata(self, sample_html_file):
        """Test that links have href in metadata."""
        parser = HtmlParser(str(sample_html_file))
        structure = parser.extract_structure()

        links = [e for e in structure if e["element_type"] == "link"]

        assert len(links) > 0
        assert "href" in links[0]["metadata"]
        assert links[0]["metadata"]["href"] == "https://example.com"


class TestHtmlParserEdgeCases:
    """Edge case tests for HtmlParser."""

    def test_html_parser_empty_file(self, temp_dir):
        """Test parsing empty HTML file."""
        file_path = temp_dir / "empty.html"
        file_path.write_text("<html><body></body></html>", encoding="utf-8")

        parser = HtmlParser(str(file_path))
        result = parser.parse()

        assert result.success is True
        assert result.text == ""

    def test_html_parser_missing_file(self):
        """Test parsing non-existent file."""
        with pytest.raises(DocumentNotFoundError):
            HtmlParser("/nonexistent/file.html")

    def test_html_parser_malformed_html(self, temp_dir):
        """Test parsing malformed HTML."""
        file_path = temp_dir / "malformed.html"
        file_path.write_text("<html><p>Unclosed tag", encoding="utf-8")

        parser = HtmlParser(str(file_path))
        result = parser.parse()

        # BeautifulSoup is tolerant, should still parse
        assert result.success is True

    def test_html_parser_encoding_detection(self, temp_dir):
        """Test encoding detection for HTML files."""
        file_path = temp_dir / "encoded.html"
        # UTF-8 encoded content with Cyrillic
        content = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Тест</title></head>
<body><p>Привет мир!</p></body>
</html>"""
        file_path.write_text(content, encoding="utf-8")

        parser = HtmlParser(str(file_path))
        result = parser.parse()

        assert "Привет мир!" in result.text

    def test_html_parser_explicit_encoding(self, temp_dir):
        """Test parsing with explicit encoding option."""
        file_path = temp_dir / "encoded.html"
        content = """<!DOCTYPE html>
<html><body><p>Test</p></body></html>"""
        file_path.write_text(content, encoding="utf-8")

        parser = HtmlParser(str(file_path), encoding="utf-8")
        result = parser.parse()

        assert result.success is True

    def test_html_parser_html_extension(self, temp_dir):
        """Test parsing .htm extension."""
        file_path = temp_dir / "test.htm"
        file_path.write_text("<html><body><p>Test</p></body></html>", encoding="utf-8")

        parser = HtmlParser(str(file_path))
        result = parser.parse()

        assert result.success is True

    def test_html_parser_case_insensitive_tags(self, temp_dir):
        """Test parsing HTML with mixed case tags."""
        file_path = temp_dir / "mixed.html"
        file_path.write_text(
            "<HTML><BODY><P>Test</P><p>Another</p></BODY></HTML>",
            encoding="utf-8",
        )

        parser = HtmlParser(str(file_path))
        result = parser.parse()

        assert result.success is True

    def test_html_parser_nested_elements(self, temp_dir):
        """Test parsing nested HTML elements."""
        file_path = temp_dir / "nested.html"
        content = """<!DOCTYPE html>
<html>
<body>
    <div>
        <p>Outer <strong>bold <em>italic</em></strong> text</p>
    </div>
</body>
</html>"""
        file_path.write_text(content, encoding="utf-8")

        parser = HtmlParser(str(file_path))
        text = parser.extract_text()

        assert "Outer" in text
        assert "bold" in text
        assert "italic" in text

    def test_html_parser_whitespace_handling(self, temp_dir):
        """Test handling of whitespace in HTML."""
        file_path = temp_dir / "whitespace.html"
        content = """<!DOCTYPE html>
<html>
<body>
    <p>
        Lots of
        whitespace
    </p>
</body>
</html>"""
        file_path.write_text(content, encoding="utf-8")

        parser = HtmlParser(str(file_path))
        text = parser.extract_text()

        assert "Lots of" in text
        assert "whitespace" in text

    def test_html_parser_result_has_quality_metrics(self, sample_html_file):
        """Test that parse result includes quality metrics."""
        parser = HtmlParser(str(sample_html_file))
        result = parser.parse()

        assert "quality" in result.to_dict()
        assert "overall_score" in result.quality
        assert 0.0 <= result.quality["overall_score"] <= 1.0

    def test_html_parser_result_has_file_metrics(self, sample_html_file):
        """Test that parse result includes file metrics."""
        parser = HtmlParser(str(sample_html_file))
        result = parser.parse()

        assert "file_metrics" in result.to_dict()
        assert result.file_metrics["file_name"] == sample_html_file.name

    def test_html_parser_result_has_semantic_blocks(self, sample_html_file):
        """Test that parse result includes semantic blocks."""
        parser = HtmlParser(str(sample_html_file))
        result = parser.parse()

        assert len(result.semantic_blocks) > 0

    def test_html_parser_result_has_raw_data(self, sample_html_file):
        """Test that parse result includes raw_data."""
        parser = HtmlParser(str(sample_html_file))
        result = parser.parse()

        assert "raw_data" in result.to_dict()
        assert "semantic_summary" in result.raw_data
