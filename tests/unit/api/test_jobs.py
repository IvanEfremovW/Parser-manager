"""
Юнит-тесты для управления очередью задач.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from parser_manager.api.jobs import JobRecord, ParseJobQueue


class TestJobRecord:
    """Тесты для dataclass JobRecord."""

    def test_job_record_creation(self):
        """Тест создания JobRecord."""
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
        """Тест создания JobRecord с webhook URL."""
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
        """Тест конвертации JobRecord в словарь."""
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
        """Тест что datetime поля форматируются как ISO строки."""
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
        """Тест что temp_file_path исключается из вывода dict."""
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
        """Тест что None result исключается из вывода dict."""
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
    """Тесты для класса ParseJobQueue."""

    @pytest.fixture
    def job_queue(self):
        """Создать свежую очередь задач."""
        return ParseJobQueue()

    @pytest.mark.asyncio
    async def test_queue_start(self, job_queue):
        """Тест запуска очереди задач."""
        await job_queue.start()

        assert job_queue._worker_task is not None
        assert not job_queue._worker_task.done()

    @pytest.mark.asyncio
    async def test_queue_stop(self, job_queue):
        """Тест остановки очереди задач."""
        await job_queue.start()
        await job_queue.stop()

        assert job_queue._worker_task.done()

    @pytest.mark.asyncio
    async def test_enqueue_job(self, job_queue):
        """Тест добавления задачи в очередь."""
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
        """Тест получения задачи по ID."""
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
        """Тест получения несуществующей задачи."""
        retrieved = job_queue.get_job("nonexistent")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_worker_processes_job(self, job_queue, mocker):
        """Тест что worker обрабатывает задачи."""
        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync",
            return_value={"text": "parsed", "success": True},
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

        # Дождаться обработки
        await asyncio.sleep(0.5)

        mock_parse.assert_called_once()
        assert job.status == "done"
        assert job.result is not None

    @pytest.mark.asyncio
    async def test_worker_handles_errors(self, job_queue, mocker):
        """Тест что worker обрабатывает ошибки парсинга."""
        mocker.patch(
            "parser_manager.api.jobs.parse_file_sync", side_effect=Exception("Parsing failed")
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

        # Дождаться обработки
        await asyncio.sleep(0.5)

        assert job.status == "failed"
        assert job.error is not None

    @pytest.mark.asyncio
    async def test_worker_cleans_temp_file(self, job_queue, mocker, temp_dir):
        """Тест что worker очищает временный файл после обработки."""
        temp_file = temp_dir / "test.html"
        temp_file.write_text("test content")

        mocker.patch("parser_manager.api.jobs.parse_file_sync", return_value={"success": True})

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

        # Дождаться обработки
        await asyncio.sleep(0.5)

        # Временный файл должен быть удалён
        assert not temp_file.exists()

    @pytest.mark.asyncio
    async def test_webhook_sent_on_completion(self, job_queue, mocker):
        """Тест что webhook отправляется при завершении задачи."""
        mocker.patch("parser_manager.api.jobs.parse_file_sync", return_value={"success": True})
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

        # Дождаться обработки
        await asyncio.sleep(0.5)

        mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_not_sent_without_url(self, job_queue, mocker):
        """Тест что webhook не отправляется когда URL не указан."""
        mocker.patch("parser_manager.api.jobs.parse_file_sync", return_value={"success": True})
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

        # Дождаться обработки
        await asyncio.sleep(0.5)

        mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_webhook_sent_on_failure(self, job_queue, mocker):
        """Тест что webhook отправляется при ошибке задачи."""
        mocker.patch("parser_manager.api.jobs.parse_file_sync", side_effect=Exception("Error"))
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

        # Дождаться обработки
        await asyncio.sleep(0.5)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["status"] == "failed"
        assert "error" in call_args[1]["json"]


class TestParseJobQueueEdgeCases:
    """Тесты граничных случаев для ParseJobQueue."""

    @pytest.mark.asyncio
    async def test_multiple_jobs_queued(self, mocker):
        """Тест постановки нескольких задач в очередь."""
        from parser_manager.api.jobs import ParseJobQueue

        queue = ParseJobQueue()

        mock_parse = mocker.patch(
            "parser_manager.api.jobs.parse_file_sync", return_value={"success": True}
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

        # Дождаться обработки всех
        await asyncio.sleep(1)

        assert mock_parse.call_count == 5
        await queue.stop()

    @pytest.mark.asyncio
    async def test_queue_restart(self, mocker):
        """Тест перезапуска очереди."""
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
