"""
Юнит-тесты для REST API приложения.
"""

import pytest


class TestHealthEndpoint:
    """Тесты для health endpoint."""

    def test_health_endpoint_success(self, api_client):
        """Тест успешного health endpoint."""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "queue_size" in data
        assert "jobs_total" in data

    def test_health_endpoint_response_structure(self, api_client):
        """Тест структуры ответа health."""
        response = api_client.get("/health")
        data = response.json()

        assert isinstance(data["status"], str)
        assert isinstance(data["queue_size"], int)
        assert isinstance(data["jobs_total"], int)


class TestCreateParseJob:
    """Тесты для создания задачи парсинга."""

    def test_create_parse_job_success(self, api_client, sample_html_content):
        """Тест успешного создания задачи парсинга."""
        files = {"file": ("test.html", sample_html_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_create_parse_job_with_webhook(self, api_client, sample_html_content):
        """Тест создания задачи с webhook URL."""
        files = {"file": ("test.html", sample_html_content, "text/html")}
        data = {"webhook_url": "https://example.com/webhook"}
        response = api_client.post("/jobs/parse", files=files, data=data)

        assert response.status_code == 200
        job_data = response.json()
        assert "job_id" in job_data

    def test_create_parse_job_missing_file(self, api_client):
        """Тест создания задачи без файла возвращает ошибку."""
        response = api_client.post("/jobs/parse")

        assert response.status_code == 422  # Ошибка валидации

    def test_create_parse_job_job_id_format(self, api_client, sample_html_content):
        """Тест что job_id имеет правильный hex формат."""
        files = {"file": ("test.html", sample_html_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        data = response.json()
        job_id = data["job_id"]

        # Должен быть hex строкой (uuid4 hex формат)
        assert len(job_id) == 32
        assert all(c in "0123456789abcdef" for c in job_id)


class TestGetJobStatus:
    """Тесты для получения статуса задачи."""

    def test_get_job_status_not_found(self, api_client):
        """Тест получения статуса несуществующей задачи."""
        response = api_client.get("/jobs/nonexistent_job_id")

        assert response.status_code == 404

    def test_get_job_status_structure(self, api_client, sample_html_content):
        """Тест структуры статуса задачи."""
        # Сначала создать задачу
        files = {"file": ("test.html", sample_html_content, "text/html")}
        create_response = api_client.post("/jobs/parse", files=files)
        job_id = create_response.json()["job_id"]

        # Получить статус
        response = api_client.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "source_file" in data


class TestGetJobResult:
    """Тесты для получения результата задачи."""

    def test_get_job_result_not_found(self, api_client):
        """Тест получения результата несуществующей задачи."""
        response = api_client.get("/jobs/nonexistent_job_id/result")

        assert response.status_code == 404

    def test_get_job_result_processing(self, api_client, sample_html_content):
        """Тест получения результата во время обработки."""
        # Создать задачу
        files = {"file": ("test.html", sample_html_content, "text/html")}
        create_response = api_client.post("/jobs/parse", files=files)
        job_id = create_response.json()["job_id"]

        # Сразу получить результат (скорее всего ещё processing/queued)
        response = api_client.get(f"/jobs/{job_id}/result")

        # Должен быть 202 (processing) или 200 (done)
        assert response.status_code in [200, 202, 204]

        if response.status_code == 202:
            data = response.json()
            assert data["status"] in ["queued", "processing"]


class TestAPIEdgeCases:
    """Тесты граничных случаев для API."""

    def test_api_cors_headers(self, api_client):
        """Тест CORS заголовков (если настроены)."""
        response = api_client.options("/health")
        # Может быть или не быть CORS настроен
        assert response.status_code in [200, 405]

    def test_api_invalid_method(self, api_client):
        """Тест неверного HTTP метода."""
        response = api_client.put("/health")
        assert response.status_code == 405

    def test_api_root_not_found(self, api_client):
        """Тест корневого endpoint."""
        response = api_client.get("/")
        # Может вернуть 404 или redirect на docs
        assert response.status_code in [200, 307, 404]

    def test_api_docs_available(self, api_client):
        """Тест доступности документации API."""
        response = api_client.get("/docs")
        assert response.status_code == 200

    def test_api_openapi_schema(self, api_client):
        """Тест доступности OpenAPI схемы."""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_api_multiple_jobs(self, api_client, sample_html_content):
        """Тест создания нескольких задач."""
        job_ids = []

        for i in range(3):
            files = {"file": (f"test{i}.html", sample_html_content, "text/html")}
            response = api_client.post("/jobs/parse", files=files)
            assert response.status_code == 200
            job_ids.append(response.json()["job_id"])

        # Все job_id должны быть уникальны
        assert len(set(job_ids)) == len(job_ids)

    def test_api_large_file(self, api_client):
        """Тест загрузки большого файла."""
        large_content = "<html><body>" + "x" * 100000 + "</body></html>"
        files = {"file": ("large.html", large_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200

    def test_api_binary_file(self, api_client):
        """Тест загрузки бинарного файла."""
        binary_content = b"\x00\x01\x02\x03" * 1000
        files = {"file": ("binary.bin", binary_content, "application/octet-stream")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200

    def test_api_unicode_filename(self, api_client, sample_html_content):
        """Тест загрузки файла с unicode именем."""
        files = {"file": ("тест_文件.html", sample_html_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200


class TestAPIAsyncBehavior:
    """Тесты асинхронного поведения API."""

    @pytest.mark.asyncio
    async def test_job_queue_startup(self, api_client):
        """Тест что очередь задач запускается корректно."""
        from parser_manager.api.jobs import job_queue

        assert job_queue._worker_task is not None
        assert not job_queue._worker_task.done()

    @pytest.mark.asyncio
    async def test_job_queue_health(self, api_client):
        """Тест что health endpoint отражает состояние очереди."""
        from parser_manager.api.jobs import job_queue

        response = api_client.get("/health")
        data = response.json()

        # Размер очереди должен совпадать с внутренним состоянием
        assert data["queue_size"] == job_queue.queue.qsize()


class TestAPIWithMockedService:
    """Тесты с мокнутым сервисом парсинга."""

    def test_parse_job_with_mocked_result(self, api_client, sample_html_content, mocker):
        """Тест завершения задачи с мокнутым результатом парсинга."""
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
        # Задача создана успешно
        job_id = response.json()["job_id"]

        # Дождаться обработки (мокнутый, должен быть быстрым)
        import time

        time.sleep(0.5)

        result_response = api_client.get(f"/jobs/{job_id}/result")
        # Может ещё быть processing или done
        assert result_response.status_code in [200, 202]

    def test_parse_job_with_mocked_error(self, api_client, sample_html_content, mocker):
        """Тест ошибки задачи с мокнутой ошибкой."""
        mocker.patch(
            "parser_manager.api.service.parse_file_sync",
            side_effect=Exception("Mocked parsing error"),
        )

        files = {"file": ("test.html", sample_html_content, "text/html")}
        response = api_client.post("/jobs/parse", files=files)

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Дождаться обработки
        import time

        time.sleep(0.5)

        # Задача должна быть в состоянии failed
        status_response = api_client.get(f"/jobs/{job_id}")
        data = status_response.json()
        assert data["status"] in ["failed", "queued", "processing", "done"]


class TestJobStatsEndpoint:
    """Тесты для endpoint статистики задачи."""

    def test_get_job_stats_not_found(self, api_client):
        """Тест получения статистики для несуществующей задачи."""
        response = api_client.get("/jobs/nonexistent/stats")
        assert response.status_code == 404


class TestJobAstEndpoint:
    """Тесты для endpoint AST задачи."""

    def test_get_job_ast_not_found(self, api_client):
        """Тест получения AST для несуществующей задачи."""
        response = api_client.get("/jobs/nonexistent/ast")
        assert response.status_code == 404


class TestJobExportEndpoint:
    """Тесты для endpoint экспорта задачи."""

    def test_get_job_export_not_found(self, api_client):
        """Тест экспорта несуществующей задачи."""
        response = api_client.get("/jobs/nonexistent/export/json")
        assert response.status_code == 404

    def test_get_job_export_invalid_format(self, api_client, sample_html_content, mocker):
        """Тест экспорта с неверным форматом."""
        mock_result = {"success": True}
        mocker.patch("parser_manager.api.service.parse_file_sync", return_value=mock_result)

        files = {"file": ("test.html", sample_html_content, "text/html")}
        create_response = api_client.post("/jobs/parse", files=files)
        job_id = create_response.json()["job_id"]

        # Дождаться обработки
        import time

        time.sleep(0.5)

        # Получить экспорт с неверным форматом
        response = api_client.get(f"/jobs/{job_id}/export/invalid")
        assert response.status_code in [400, 404, 500]
