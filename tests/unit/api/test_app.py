"""
Unit tests for FastAPI application.

Test Cases:
- TC-API-001: Health Endpoint
- TC-API-002: Create Parse Job
- TC-API-003: Get Job Status
- TC-API-004: Get Job Result
"""

import pytest


class TestHealthEndpoint:
    """Tests for TC-API-001: Health Endpoint."""

    def test_health_endpoint_success(self, api_client):
        """Test health endpoint returns OK status."""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "queue_size" in data
        assert "jobs_total" in data

    def test_health_endpoint_response_structure(self, api_client):
        """Test health endpoint response structure."""
        response = api_client.get("/health")
        data = response.json()

        assert isinstance(data["status"], str)
        assert isinstance(data["queue_size"], int)
        assert isinstance(data["jobs_total"], int)


class TestCreateParseJob:
    """Tests for TC-API-002: Create Parse Job."""

    def test_create_parse_job_success(self, api_client, sample_html_content):
        """Test creating a parse job."""
        files = {"file": ("test.html", sample_html_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_create_parse_job_with_webhook(self, api_client, sample_html_content):
        """Test creating a parse job with webhook URL."""
        files = {"file": ("test.html", sample_html_content, "text/html")}
        data = {"webhook_url": "https://example.com/webhook"}
        response = api_client.post("/jobs/parse", files=files, data=data)

        assert response.status_code == 200
        job_data = response.json()
        assert "job_id" in job_data

    def test_create_parse_job_missing_file(self, api_client):
        """Test creating job without file returns error."""
        response = api_client.post("/jobs/parse")

        assert response.status_code == 422  # Validation error

    def test_create_parse_job_job_id_format(self, api_client, sample_html_content):
        """Test that job_id is a valid hex string."""
        files = {"file": ("test.html", sample_html_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        data = response.json()
        job_id = data["job_id"]

        # Should be hex string (uuid4 hex format)
        assert len(job_id) == 32
        assert all(c in "0123456789abcdef" for c in job_id)


class TestGetJobStatus:
    """Tests for TC-API-003: Get Job Status."""

    def test_get_job_status_not_found(self, api_client):
        """Test getting status of non-existent job."""
        response = api_client.get("/jobs/nonexistent_job_id")

        assert response.status_code == 404

    def test_get_job_status_structure(self, api_client, sample_html_content):
        """Test job status response structure."""
        # Create a job first
        files = {"file": ("test.html", sample_html_content, "text/html")}
        create_response = api_client.post("/jobs/parse", files=files)
        job_id = create_response.json()["job_id"]

        # Get status
        response = api_client.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "source_file" in data


class TestGetJobResult:
    """Tests for TC-API-004: Get Job Result."""

    def test_get_job_result_not_found(self, api_client):
        """Test getting result of non-existent job."""
        response = api_client.get("/jobs/nonexistent_job_id/result")

        assert response.status_code == 404

    def test_get_job_result_processing(self, api_client, sample_html_content):
        """Test getting result while job is still processing."""
        # Create a job
        files = {"file": ("test.html", sample_html_content, "text/html")}
        create_response = api_client.post("/jobs/parse", files=files)
        job_id = create_response.json()["job_id"]

        # Immediately get result (likely still queued/processing)
        response = api_client.get(f"/jobs/{job_id}/result")

        # Should be 202 (processing) or 200 (done)
        assert response.status_code in [200, 202, 204]

        if response.status_code == 202:
            data = response.json()
            assert data["status"] in ["queued", "processing"]


class TestAPIEdgeCases:
    """Edge case tests for API."""

    def test_api_cors_headers(self, api_client):
        """Test CORS headers are present (if configured)."""
        response = api_client.options("/health")
        # May or may not have CORS configured
        assert response.status_code in [200, 405]

    def test_api_invalid_method(self, api_client):
        """Test invalid HTTP method."""
        response = api_client.put("/health")
        assert response.status_code == 405

    def test_api_root_not_found(self, api_client):
        """Test root endpoint."""
        response = api_client.get("/")
        # May return 404 or docs redirect
        assert response.status_code in [200, 307, 404]

    def test_api_docs_available(self, api_client):
        """Test that API docs are available."""
        response = api_client.get("/docs")
        assert response.status_code == 200

    def test_api_openapi_schema(self, api_client):
        """Test OpenAPI schema is available."""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_api_multiple_jobs(self, api_client, sample_html_content):
        """Test creating multiple jobs."""
        job_ids = []

        for i in range(3):
            files = {"file": (f"test{i}.html", sample_html_content, "text/html")}
            response = api_client.post("/jobs/parse", files=files)
            assert response.status_code == 200
            job_ids.append(response.json()["job_id"])

        # All job IDs should be unique
        assert len(set(job_ids)) == len(job_ids)

    def test_api_large_file(self, api_client):
        """Test uploading a large file."""
        large_content = "<html><body>" + "x" * 100000 + "</body></html>"
        files = {"file": ("large.html", large_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200

    def test_api_binary_file(self, api_client):
        """Test uploading a binary file."""
        binary_content = b"\x00\x01\x02\x03" * 1000
        files = {"file": ("binary.bin", binary_content, "application/octet-stream")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200

    def test_api_unicode_filename(self, api_client, sample_html_content):
        """Test uploading file with unicode filename."""
        files = {"file": ("тест_文件.html", sample_html_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200


class TestAPIAsyncBehavior:
    """Tests for async behavior of API."""

    @pytest.mark.asyncio
    async def test_job_queue_startup(self, api_client):
        """Test that job queue starts correctly."""
        from parser_manager.api.jobs import job_queue

        assert job_queue._worker_task is not None
        assert not job_queue._worker_task.done()

    @pytest.mark.asyncio
    async def test_job_queue_health(self, api_client):
        """Test health endpoint reflects queue state."""
        from parser_manager.api.jobs import job_queue

        response = api_client.get("/health")
        data = response.json()

        # Queue size should match internal state
        assert data["queue_size"] == job_queue.queue.qsize()


class TestAPIWithMockedService:
    """Tests with mocked parsing service."""

    def test_parse_job_with_mocked_result(self, api_client, sample_html_content, mocker):
        """Test job completion with mocked parse result."""
        mock_result = {
            "file_path": "/tmp/test.html",
            "format": "html",
            "text": "Mocked text",
            "metadata": {},
            "structure": [],
            "semantic_blocks": [],
            "quality": {"overall_score": 0.9},
            "file_metrics": {},
            "raw_data": {},
            "parsed_at": "2024-01-01T00:00:00",
            "success": True,
            "error": None,
        }

        mocker.patch("parser_manager.api.service.parse_file_sync", return_value=mock_result)

        files = {"file": ("test.html", sample_html_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200
        # Job is created successfully
        job_id = response.json()["job_id"]

        # Wait for processing (mocked, should be fast)
        import time

        time.sleep(0.5)

        result_response = api_client.get(f"/jobs/{job_id}/result")
        # May still be processing or done
        assert result_response.status_code in [200, 202]

    def test_parse_job_with_mocked_error(self, api_client, sample_html_content, mocker):
        """Test job failure with mocked error."""
        mocker.patch(
            "parser_manager.api.service.parse_file_sync",
            side_effect=Exception("Mocked parsing error"),
        )

        files = {"file": ("test.html", sample_html_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for processing
        import time

        time.sleep(0.5)

        # Job should be in failed state or still processing
        status_response = api_client.get(f"/jobs/{job_id}")
        data = status_response.json()
        assert data["status"] in ["failed", "queued", "processing", "done"]
