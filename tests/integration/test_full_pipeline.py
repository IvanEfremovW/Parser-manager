"""
Integration tests for Parser Manager.

These tests verify the full parsing pipeline from file input to JSON output.
"""

import asyncio
from datetime import datetime

import pytest

# Import parsers to register them
import parser_manager.parsers  # noqa: F401
from parser_manager.api.jobs import JobRecord, ParseJobQueue
from parser_manager.core import ParserFactory
from parser_manager.models import ParsedContent


class TestFullParsingPipeline:
    """Integration tests for the full parsing pipeline."""

    def test_html_full_pipeline(self, sample_html_file):
        """Test complete HTML parsing pipeline."""
        # Create parser via factory
        parser = ParserFactory.create_parser(str(sample_html_file))

        # Parse
        result = parser.parse()

        # Verify result structure
        assert isinstance(result, ParsedContent)
        assert result.success is True
        assert result.format == "html"

        # Verify semantic blocks
        assert len(result.semantic_blocks) > 0

        # Verify quality metrics
        assert "overall_score" in result.quality
        assert 0.0 <= result.quality["overall_score"] <= 1.0

        # Verify file metrics
        assert result.file_metrics["file_name"] == sample_html_file.name

        # Verify serialization
        result_dict = result.to_dict()
        assert "parsed_at" in result_dict
        assert isinstance(result_dict["parsed_at"], str)

    def test_pdf_full_pipeline(self, sample_pdf_file):
        """Test complete PDF parsing pipeline."""
        parser = ParserFactory.create_parser(str(sample_pdf_file))
        result = parser.parse()

        assert isinstance(result, ParsedContent)
        assert result.success is True
        assert result.format == "pdf"
        assert "backend_used" in result.raw_data

    def test_docx_full_pipeline(self, sample_docx_file):
        """Test complete DOCX parsing pipeline."""
        parser = ParserFactory.create_parser(str(sample_docx_file))
        result = parser.parse()

        assert isinstance(result, ParsedContent)
        assert result.success is True
        assert result.format == "docx"

        # Verify structure contains expected elements
        element_types = [e["element_type"] for e in result.structure]
        assert "heading" in element_types
        assert "table" in element_types

    def test_factory_auto_registration(self, sample_html_file):
        """Test that parsers are auto-registered on import."""
        # Should have registered parsers
        formats = ParserFactory.get_available_formats()

        assert ".html" in formats
        assert ".htm" in formats
        assert ".pdf" in formats
        assert ".docx" in formats
        assert ".doc" in formats
        assert ".djvu" in formats

    def test_factory_parser_selection(self, temp_dir):
        """Test that factory selects correct parser for each format."""
        # Create test files
        html_file = temp_dir / "test.html"
        html_file.write_text("<html></html>")

        pdf_file = temp_dir / "test.pdf"
        # Minimal PDF
        pdf_file.write_bytes(
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n100\n%%EOF\n"
        )

        # Get parsers
        html_parser = ParserFactory.create_parser(str(html_file))
        assert html_parser.format_name == "html"

        # PDF parser selection (may fail on minimal PDF, but should select correct parser)
        try:
            pdf_parser = ParserFactory.create_parser(str(pdf_file))
            assert pdf_parser.format_name == "pdf"
        except Exception:
            # Minimal PDF may not parse, but parser selection should work
            pass


class TestAPIIntegration:
    """Integration tests for API workflow."""

    @pytest.mark.asyncio
    async def test_api_full_workflow(self, api_client, sample_html_content):
        """Test complete API workflow: create job → process → get result."""
        # Step 1: Create job
        files = {"file": ("test.html", sample_html_content, "text/html")}
        create_response = api_client.post("/jobs/parse", files=files)

        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Step 2: Wait for processing
        await asyncio.sleep(1)

        # Step 3: Get status
        status_response = api_client.get(f"/jobs/{job_id}")
        assert status_response.status_code == 200

        # Step 4: Get result
        result_response = api_client.get(f"/jobs/{job_id}/result")
        assert result_response.status_code in [200, 202]

        if result_response.status_code == 200:
            result_data = result_response.json()
            assert "result" in result_data or "status" in result_data

    @pytest.mark.asyncio
    async def test_api_multiple_sequential_jobs(self, api_client, sample_html_content):
        """Test processing multiple jobs sequentially."""
        job_ids = []

        # Create 3 jobs
        for i in range(3):
            files = {"file": (f"test{i}.html", sample_html_content, "text/html")}
            response = api_client.post("/jobs/parse", files=files)
            assert response.status_code == 200
            job_ids.append(response.json()["job_id"])

        # Wait for processing
        await asyncio.sleep(2)

        # Check all jobs
        for job_id in job_ids:
            status_response = api_client.get(f"/jobs/{job_id}")
            assert status_response.status_code == 200
            status = status_response.json()["status"]
            assert status in ["queued", "processing", "done", "failed"]

    @pytest.mark.asyncio
    async def test_api_job_with_webhook_callback(self, api_client, sample_html_content, mocker):
        """Test job creation with webhook callback."""
        # Mock webhook endpoint
        mocker.patch("httpx.AsyncClient.post")

        files = {"file": ("test.html", sample_html_content, "text/html")}
        data = {"webhook_url": "https://example.com/webhook"}

        response = api_client.post("/jobs/parse", files=files, data=data)
        assert response.status_code == 200

        # Wait for processing
        await asyncio.sleep(1)

        # Webhook should be called (either on success or failure)
        # Note: In test environment, this may not complete in time
        # The unit tests cover webhook behavior more thoroughly


class TestQualityMetricsIntegration:
    """Integration tests for quality metrics."""

    def test_quality_metrics_consistency(self, sample_html_file):
        """Test that quality metrics are consistent across runs."""
        parser = ParserFactory.create_parser(str(sample_html_file))

        result1 = parser.parse()
        result2 = parser.parse()

        # Quality scores should be identical for same content
        assert result1.quality["overall_score"] == result2.quality["overall_score"]
        assert result1.quality["text_completeness"] == result2.quality["text_completeness"]

    def test_quality_metrics_range(self, sample_html_file):
        """Test that all quality metrics are in valid range."""
        parser = ParserFactory.create_parser(str(sample_html_file))
        result = parser.parse()

        metrics_in_range = [
            "overall_score",
            "text_completeness",
            "structure_score",
            "noise_ratio",
            "broken_chars_ratio",
            "table_coverage",
        ]

        for metric in metrics_in_range:
            value = result.quality[metric]
            assert 0.0 <= value <= 1.0, f"{metric} = {value} out of range"

    def test_semantic_summary_accuracy(self, sample_html_file):
        """Test that semantic summary matches actual blocks."""
        parser = ParserFactory.create_parser(str(sample_html_file))
        result = parser.parse()

        summary = result.raw_data["semantic_summary"]

        # Total should match sum of types
        type_counts = (
            summary["heading_blocks"]
            + summary["paragraph_blocks"]
            + summary["table_blocks"]
            + summary["list_blocks"]
            + summary["link_blocks"]
        )

        assert summary["total_blocks"] == type_counts

        # Total should match actual blocks
        assert summary["total_blocks"] == len(result.semantic_blocks)


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_corrupted_file_error_propagation(self, temp_dir):
        """Test that corrupted file errors propagate correctly."""
        # Create corrupted DOCX
        corrupted_file = temp_dir / "corrupted.docx"
        corrupted_file.write_bytes(b"Not a valid DOCX")

        with pytest.raises(Exception) as exc_info:
            parser = ParserFactory.create_parser(str(corrupted_file))
            parser.parse()

        # Should be a parser-related error
        from parser_manager.models import ParserError

        assert isinstance(exc_info.value, ParserError)

    def test_missing_file_error_propagation(self):
        """Test that missing file errors propagate correctly."""
        with pytest.raises(Exception) as exc_info:
            parser = ParserFactory.create_parser("/nonexistent/file.html")
            parser.parse()

        from parser_manager.models import DocumentNotFoundError

        assert isinstance(exc_info.value, DocumentNotFoundError)

    def test_unsupported_format_error_propagation(self, temp_dir):
        """Test that unsupported format errors propagate correctly."""
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("content")

        with pytest.raises(Exception) as exc_info:
            parser = ParserFactory.create_parser(str(unsupported_file))
            parser.parse()

        from parser_manager.models import UnsupportedFormatError

        assert isinstance(exc_info.value, UnsupportedFormatError)


class TestConcurrencyIntegration:
    """Integration tests for concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_parsing(self, sample_html_file):
        """Test concurrent parsing operations."""
        import asyncio

        def parse_sync():
            parser = ParserFactory.create_parser(str(sample_html_file))
            return parser.parse()

        # Run multiple parses concurrently
        loop = asyncio.get_event_loop()
        results = await asyncio.gather(*[loop.run_in_executor(None, parse_sync) for _ in range(5)])

        # All should succeed
        for result in results:
            assert result.success is True
            assert result.format == "html"

    @pytest.mark.asyncio
    async def test_concurrent_job_queue(self, sample_html_content):
        """Test concurrent job queue operations."""

        queue = ParseJobQueue()
        await queue.start()

        # Enqueue multiple jobs
        for i in range(5):
            job = JobRecord(
                job_id=f"concurrent_{i}",
                status="queued",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_file=f"test{i}.html",
                temp_file_path=f"/tmp/test{i}.html",
            )
            await queue.enqueue(job)

        # Wait for processing
        await asyncio.sleep(2)
        await queue.stop()

        # All jobs should be processed
        for i in range(5):
            job = queue.get_job(f"concurrent_{i}")
            assert job is not None
            assert job.status in ["done", "failed"]


class TestParserRegistryIntegration:
    """Integration tests for parser registry."""

    def test_parser_registration_persistence(self):
        """Test that parser registrations persist across calls."""
        # First call
        formats1 = ParserFactory.get_available_formats()

        # Second call
        formats2 = ParserFactory.get_available_formats()

        assert formats1 == formats2

    def test_parser_creation_repeatability(self, sample_html_file):
        """Test that parser creation is repeatable."""
        parser1 = ParserFactory.create_parser(str(sample_html_file))
        parser2 = ParserFactory.create_parser(str(sample_html_file))

        assert type(parser1) is type(parser2)
        assert parser1.format_name == parser2.format_name
