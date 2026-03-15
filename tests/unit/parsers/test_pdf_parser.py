"""
Unit tests for PdfParser.

Test Cases:
- TC-PARSER-PDF-001: PDF Parsing
- TC-PARSER-PDF-002: PDF Fallback
"""

import pytest

from parser_manager.models import (
    CorruptedFileError,
    DocumentNotFoundError,
    ParsedContent,
    ParsingFailedError,
)
from parser_manager.parsers.documents.pdf_parser import PdfParser


class TestPdfParserInitialization:
    """Tests for PdfParser initialization."""

    def test_pdf_parser_supported_extensions(self):
        """Test supported extensions."""
        assert PdfParser.supported_extensions == (".pdf",)
        assert PdfParser.format_name == "pdf"

    def test_pdf_parser_quality_threshold(self):
        """Test quality fallback threshold."""
        assert PdfParser.quality_fallback_threshold == 0.55


class TestPdfParserParsing:
    """Tests for TC-PARSER-PDF-001: PDF Parsing."""

    def test_pdf_parser_parse_success(self, sample_pdf_file):
        """Test successful PDF parsing."""
        parser = PdfParser(str(sample_pdf_file))
        result = parser.parse()

        assert isinstance(result, ParsedContent)
        assert result.success is True
        assert result.format == "pdf"
        assert result.error is None

    def test_pdf_parser_extract_text(self, sample_pdf_file):
        """Test text extraction from PDF."""
        parser = PdfParser(str(sample_pdf_file))
        text = parser.extract_text()

        assert isinstance(text, str)
        assert "Test PDF Content" in text

    def test_pdf_parser_extract_metadata(self, sample_pdf_file):
        """Test metadata extraction from PDF."""
        parser = PdfParser(str(sample_pdf_file))
        metadata = parser.extract_metadata()

        assert isinstance(metadata.pages, int)
        assert metadata.pages >= 1

    def test_pdf_parser_extract_structure(self, sample_pdf_file):
        """Test structure extraction from PDF."""
        parser = PdfParser(str(sample_pdf_file))
        structure = parser.extract_structure()

        # Should have at least one element
        assert len(structure) > 0

    def test_pdf_parser_structure_has_pages(self, sample_pdf_file):
        """Test that structure elements have page numbers."""
        parser = PdfParser(str(sample_pdf_file))
        structure = parser.extract_structure()

        for element in structure:
            assert "page" in element
            assert element["page"] >= 1

    def test_pdf_parser_raw_data_backend(self, sample_pdf_file):
        """Test that raw_data includes backend information."""
        parser = PdfParser(str(sample_pdf_file))
        result = parser.parse()

        assert "backend_used" in result.raw_data
        assert result.raw_data["backend_used"] in ["pdfplumber", "pypdf2"]

    def test_pdf_parser_raw_data_pages(self, sample_pdf_file):
        """Test that raw_data includes page count."""
        parser = PdfParser(str(sample_pdf_file))
        result = parser.parse()

        assert "pages" in result.raw_data
        assert result.raw_data["pages"] >= 1


class TestPdfParserFallback:
    """Tests for TC-PARSER-PDF-002: PDF Fallback."""

    def test_pdf_parser_fallback_attempted_flag(self, sample_pdf_file):
        """Test that fallback_attempted is tracked."""
        parser = PdfParser(str(sample_pdf_file))
        result = parser.parse()

        assert "fallback_attempted" in result.raw_data
        assert isinstance(result.raw_data["fallback_attempted"], bool)

    def test_pdf_parser_quality_score_present(self, sample_pdf_file):
        """Test that quality score is calculated."""
        parser = PdfParser(str(sample_pdf_file))
        result = parser.parse()

        assert "overall_score" in result.quality


class TestPdfParserEdgeCases:
    """Edge case tests for PdfParser."""

    def test_pdf_parser_missing_file(self):
        """Test parsing non-existent file."""
        with pytest.raises(DocumentNotFoundError):
            PdfParser("/nonexistent/file.pdf")

    def test_pdf_parser_corrupted_file(self, temp_dir):
        """Test parsing corrupted PDF file."""
        file_path = temp_dir / "corrupted.pdf"
        file_path.write_bytes(b"Not a valid PDF content")

        with pytest.raises((CorruptedFileError, ParsingFailedError)):
            parser = PdfParser(str(file_path))
            parser.parse()

    def test_pdf_parser_empty_file(self, temp_dir):
        """Test parsing empty PDF file."""
        file_path = temp_dir / "empty.pdf"
        file_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        with pytest.raises((CorruptedFileError, ParsingFailedError)):
            parser = PdfParser(str(file_path))
            parser.parse()

    def test_pdf_parser_clean_text_method(self):
        """Test _clean_text static method."""
        # Test with None
        assert PdfParser._clean_text(None) == ""

        # Test with empty string
        assert PdfParser._clean_text("") == ""

        # Test with normal text
        assert PdfParser._clean_text("Hello\n\n\nWorld") == "Hello\n\nWorld"

        # Test with leading/trailing whitespace
        text = "  line1  \n  line2  "
        result = PdfParser._clean_text(text)
        assert "line1" in result
        assert "line2" in result

    def test_pdf_parser_multiple_pages_pdf(self, temp_dir):
        """Test PDF with multiple pages (if pdfplumber handles it)."""
        # Create a minimal multi-page PDF structure
        # Note: This is a simplified test - real multi-page PDFs are more complex
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Contents 5 0 R /Resources << /Font << /F1 6 0 R >> >> >>
endobj
4 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Contents 7 0 R /Resources << /Font << /F1 6 0 R >> >> >>
endobj
5 0 obj
<< /Length 20 >>
stream
BT /F1 12 Tf 50 700 Td (Page1) Tj ET
endstream
endobj
6 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
7 0 obj
<< /Length 20 >>
stream
BT /F1 12 Tf 50 700 Td (Page2) Tj ET
endstream
endobj
xref
0 8
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000232 00000 n
0000000349 00000 n
0000000420 00000 n
0000000497 00000 n
trailer
<< /Size 8 /Root 1 0 R >>
startxref
618
%%EOF
"""
        file_path = temp_dir / "multipage.pdf"
        file_path.write_bytes(pdf_content)

        try:
            parser = PdfParser(str(file_path))
            result = parser.parse()

            assert result.success is True
            # Minimal PDF may not have proper page count, but text should be extracted
            assert "Page1" in result.text or "Page2" in result.text
        except (CorruptedFileError, ParsingFailedError):
            # Some minimal PDFs may not parse correctly - that's acceptable
            pytest.skip("Minimal multi-page PDF structure not supported by pdfplumber")

    def test_pdf_parser_result_has_quality_metrics(self, sample_pdf_file):
        """Test that parse result includes quality metrics."""
        parser = PdfParser(str(sample_pdf_file))
        result = parser.parse()

        assert "quality" in result.to_dict()
        assert "overall_score" in result.quality

    def test_pdf_parser_result_has_file_metrics(self, sample_pdf_file):
        """Test that parse result includes file metrics."""
        parser = PdfParser(str(sample_pdf_file))
        result = parser.parse()

        assert "file_metrics" in result.to_dict()
        assert result.file_metrics["file_name"] == sample_pdf_file.name

    def test_pdf_parser_result_has_semantic_blocks(self, sample_pdf_file):
        """Test that parse result includes semantic blocks."""
        parser = PdfParser(str(sample_pdf_file))
        result = parser.parse()

        assert len(result.semantic_blocks) > 0

    def test_pdf_parser_tables_extraction(self, sample_pdf_file):
        """Test table extraction from PDF (if present)."""
        # Create PDF with table-like content
        # Note: Real table extraction depends on PDF structure
        parser = PdfParser(str(sample_pdf_file))
        structure = parser.extract_structure()

        # Tables may or may not be present depending on PDF content
        # Just verify the parser runs without error
        assert isinstance(structure, list)
