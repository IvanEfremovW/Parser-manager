"""
Unit tests for job queue management.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from parser_manager.api.jobs import JobRecord, ParseJobQueue


class TestJobRecord:
    """Tests for JobRecord dataclass."""

    def test_job_record_creation(self):
        """Test creating a JobRecord."""
        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
        )

        assert job.job_id == "test123"
        assert job.status == "queued"
        assert job.webhook_url is None
        assert job.result is None
        assert job.error is None

    def test_job_record_with_webhook(self):
        """Test creating a JobRecord with webhook URL."""
        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
            webhook_url="https://example.com/webhook",
        )

        assert job.webhook_url == "https://example.com/webhook"

    def test_job_record_to_dict(self):
        """Test converting JobRecord to dictionary."""
        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="done",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
            webhook_url="https://example.com/webhook",
            result={"text": "parsed content"},
            error=None,
        )

        result = job.to_dict()

        assert result["job_id"] == "test123"
        assert result["status"] == "done"
        assert "created_at" in result
        assert "updated_at" in result
        assert result["source_file"] == "test.html"
        assert result["webhook_url"] == "https://example.com/webhook"
        assert result["error"] is None

    def test_job_record_to_dict_datetime_format(self):
        """Test that datetime fields are formatted as ISO strings."""
        now = datetime(2024, 1, 15, 10, 30, 0)
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
        )

        result = job.to_dict()

        assert result["created_at"] == "2024-01-15T10:30:00"
        assert result["updated_at"] == "2024-01-15T10:30:00"

    def test_job_record_to_dict_excludes_temp_path(self):
        """Test that temp_file_path is excluded from dict output."""
        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
        )

        result = job.to_dict()

        assert "temp_file_path" not in result

    def test_job_record_to_dict_excludes_result_when_none(self):
        """Test that None result is excluded from dict output."""
        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
            result=None,
        )

        result = job.to_dict()

        assert "result" not in result


class TestParseJobQueue:
    """Tests for ParseJobQueue class."""

    @pytest.fixture
    def job_queue(self):
        """Create a fresh job queue."""
        return ParseJobQueue()

    @pytest.mark.asyncio
    async def test_queue_start(self, job_queue):
        """Test starting the job queue."""
        await job_queue.start()

        assert job_queue._worker_task is not None
        assert not job_queue._worker_task.done()

    @pytest.mark.asyncio
    async def test_queue_stop(self, job_queue):
        """Test stopping the job queue."""
        await job_queue.start()
        await job_queue.stop()

        assert job_queue._worker_task.done()

    @pytest.mark.asyncio
    async def test_enqueue_job(self, job_queue):
        """Test enqueueing a job."""
        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
        )

        await job_queue.start()
        await job_queue.enqueue(job)

        assert "test123" in job_queue.jobs
        assert job_queue.queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_get_job(self, job_queue):
        """Test getting a job by ID."""
        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
        )

        await job_queue.enqueue(job)

        retrieved = job_queue.get_job("test123")
        assert retrieved is not None
        assert retrieved.job_id == "test123"

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, job_queue):
        """Test getting a non-existent job."""
        retrieved = job_queue.get_job("nonexistent")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_worker_processes_job(self, job_queue, mocker):
        """Test that worker processes jobs."""
        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync",
            return_value={"text": "parsed", "success": True}
        )

        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
        )

        await job_queue.start()
        await job_queue.enqueue(job)

        # Wait for processing
        await asyncio.sleep(0.5)

        mock_parse.assert_called_once()
        assert job.status == "done"
        assert job.result is not None

    @pytest.mark.asyncio
    async def test_worker_handles_errors(self, job_queue, mocker):
        """Test that worker handles parsing errors."""
        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync",
            side_effect=Exception("Parsing failed")
        )

        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
        )

        await job_queue.start()
        await job_queue.enqueue(job)

        # Wait for processing
        await asyncio.sleep(0.5)

        assert job.status == "failed"
        assert job.error is not None

    @pytest.mark.asyncio
    async def test_worker_cleans_temp_file(self, job_queue, mocker, temp_dir):
        """Test that worker cleans up temp file after processing."""
        temp_file = temp_dir / "test.html"
        temp_file.write_text("test content")

        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync",
            return_value={"success": True}
        )

        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path=str(temp_file),
        )

        await job_queue.start()
        await job_queue.enqueue(job)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Temp file should be deleted
        assert not temp_file.exists()

    @pytest.mark.asyncio
    async def test_webhook_sent_on_completion(self, job_queue, mocker):
        """Test that webhook is sent on job completion."""
        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync",
            return_value={"success": True}
        )
        mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)

        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
            webhook_url="https://example.com/webhook",
        )

        await job_queue.start()
        await job_queue.enqueue(job)

        # Wait for processing
        await asyncio.sleep(0.5)

        mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_not_sent_without_url(self, job_queue, mocker):
        """Test that webhook is not sent when URL is not provided."""
        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync",
            return_value={"success": True}
        )
        mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)

        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
            webhook_url=None,
        )

        await job_queue.start()
        await job_queue.enqueue(job)

        # Wait for processing
        await asyncio.sleep(0.5)

        mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_webhook_sent_on_failure(self, job_queue, mocker):
        """Test that webhook is sent on job failure."""
        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync",
            side_effect=Exception("Error")
        )
        mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)

        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
            webhook_url="https://example.com/webhook",
        )

        await job_queue.start()
        await job_queue.enqueue(job)

        # Wait for processing
        await asyncio.sleep(0.5)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["status"] == "failed"
        assert "error" in call_args[1]["json"]


class TestParseJobQueueEdgeCases:
    """Edge case tests for ParseJobQueue."""

    @pytest.mark.asyncio
    async def test_multiple_jobs_queued(self, mocker):
        """Test queueing multiple jobs."""
        from parser_manager.api.jobs import ParseJobQueue
        
        queue = ParseJobQueue()
        
        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync",
            return_value={"success": True}
        )

        await queue.start()

        for i in range(5):
            now = datetime.utcnow()
            job = JobRecord(
                job_id=f"job{i}",
                status="queued",
                created_at=now,
                updated_at=now,
                source_file=f"test{i}.html",
                temp_file_path=f"/tmp/test{i}.html",
            )
            await queue.enqueue(job)

        assert queue.queue.qsize() == 5

        # Wait for all to process
        await asyncio.sleep(1)

        assert mock_parse.call_count == 5
        await queue.stop()

    @pytest.mark.asyncio
    async def test_queue_restart(self, mocker):
        """Test restarting the queue."""
        from parser_manager.api.jobs import ParseJobQueue
        
        queue = ParseJobQueue()
        
        await queue.start()
        first_task = queue._worker_task

        await queue.stop()
        await queue.start()

        second_task = queue._worker_task

        assert first_task.done()
        assert not second_task.done()
        await queue.stop()

    @pytest.mark.asyncio
    async def test_get_job_during_processing(self, mocker):
        """Test getting job while it's being processed."""
        from parser_manager.api.jobs import ParseJobQueue
        
        queue = ParseJobQueue()
        
        # Create a slow mock
        async def slow_parse(*args):
            await asyncio.sleep(0.2)
            return {"success": True}

        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync",
            side_effect=lambda *args: asyncio.run(slow_parse())
        )

        now = datetime.utcnow()
        job = JobRecord(
            job_id="test123",
            status="queued",
            created_at=now,
            updated_at=now,
            source_file="test.html",
            temp_file_path="/tmp/test.html",
        )

        await queue.start()
        await queue.enqueue(job)

        # Check status during processing
        await asyncio.sleep(0.1)
        retrieved = queue.get_job("test123")
        assert retrieved is not None
        assert retrieved.status in ["queued", "processing", "done"]
        await queue.stop()
