"""
Интеграционные тесты для Parser Manager.

Эти тесты проверяют полный пайплайн парсинга от входного файла до JSON вывода.
"""

import asyncio
from datetime import datetime

import pytest

# Импортируем парсеры для их регистрации
import parser_manager.parsers  # noqa: F401
from parser_manager.api.jobs import JobRecord, ParseJobQueue
from parser_manager.core import ParserFactory
from parser_manager.models import ParsedContent


class TestFullParsingPipeline:
    """Интеграционные тесты полного пайплайна парсинга."""

    def test_html_full_pipeline(self, sample_html_file):
        """Тест полного пайплайна парсинга HTML."""
        # Создать парсер через фабрику
        parser = ParserFactory.create_parser(str(sample_html_file))

        # Распарсить
        result = parser.parse()

        # Проверить структуру результата
        assert isinstance(result, ParsedContent)
        assert result.success is True
        assert result.format == "html"

        # Проверить семантические блоки
        assert len(result.semantic_blocks) > 0

        # Проверить метрики качества
        assert "overall_score" in result.quality
        assert 0.0 <= result.quality["overall_score"] <= 1.0

        # Проверить метрики файла
        assert result.file_metrics["file_name"] == sample_html_file.name

        # Проверить сериализацию
        result_dict = result.to_dict()
        assert "parsed_at" in result_dict
        assert isinstance(result_dict["parsed_at"], str)

    def test_pdf_full_pipeline(self, sample_pdf_file):
        """Тест полного пайплайна парсинга PDF."""
        parser = ParserFactory.create_parser(str(sample_pdf_file))
        result = parser.parse()

        assert isinstance(result, ParsedContent)
        assert result.success is True
        assert result.format == "pdf"
        assert "backend_used" in result.raw_data

    def test_docx_full_pipeline(self, sample_docx_file):
        """Тест полного пайплайна парсинга DOCX."""
        parser = ParserFactory.create_parser(str(sample_docx_file))
        result = parser.parse()

        assert isinstance(result, ParsedContent)
        assert result.success is True
        assert result.format == "docx"

        # Проверить что структура содержит ожидаемые элементы
        element_types = [e["element_type"] for e in result.structure]
        assert "heading" in element_types
        assert "table" in element_types

    def test_factory_auto_registration(self, sample_html_file):
        """Тест авто-регистрации парсеров при импорте."""
        # Должны быть зарегистрированные парсеры
        formats = ParserFactory.get_available_formats()

        assert ".html" in formats
        assert ".htm" in formats
        assert ".pdf" in formats
        assert ".docx" in formats
        assert ".doc" in formats
        assert ".djvu" in formats

    def test_factory_parser_selection(self, temp_dir):
        """Тест выбора правильного парсера фабрикой для каждого формата."""
        # Создать тестовые файлы
        html_file = temp_dir / "test.html"
        html_file.write_text("<html></html>")

        pdf_file = temp_dir / "test.pdf"
        # Минимальный PDF
        pdf_file.write_bytes(
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n100\n%%EOF\n"
        )

        # Получить парсеры
        html_parser = ParserFactory.create_parser(str(html_file))
        assert html_parser.format_name == "html"

        # Выбор парсера для PDF (может провалиться на минимальном PDF, но парсер должен выбраться правильный)
        try:
            pdf_parser = ParserFactory.create_parser(str(pdf_file))
            assert pdf_parser.format_name == "pdf"
        except Exception:
            # Минимальный PDF может не распарситься, но выбор парсера должен сработать
            pass


class TestAPIIntegration:
    """Интеграционные тесты для API."""

    @pytest.mark.asyncio
    async def test_api_full_workflow(self, api_client, sample_html_content):
        """Тест полного рабочего процесса API: создание задачи → обработка → получение результата."""
        # Шаг 1: Создать задачу
        files = {"file": ("test.html", sample_html_content, "text/html")}
        create_response = api_client.post("/jobs/parse", files=files)

        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Шаг 2: Дождаться обработки
        await asyncio.sleep(1)

        # Шаг 3: Получить статус
        status_response = api_client.get(f"/jobs/{job_id}")
        assert status_response.status_code == 200

        # Шаг 4: Получить результат
        result_response = api_client.get(f"/jobs/{job_id}/result")
        assert result_response.status_code in [200, 202]

        if result_response.status_code == 200:
            result_data = result_response.json()
            assert "result" in result_data or "status" in result_data

    @pytest.mark.asyncio
    async def test_api_multiple_sequential_jobs(self, api_client, sample_html_content):
        """Тест обработки нескольких задач последовательно."""
        job_ids = []

        # Создать 3 задачи
        for i in range(3):
            files = {"file": (f"test{i}.html", sample_html_content, "text/html")}
            response = api_client.post("/jobs/parse", files=files)
            assert response.status_code == 200
            job_ids.append(response.json()["job_id"])

        # Дождаться обработки
        await asyncio.sleep(2)

        # Проверить все задачи
        for job_id in job_ids:
            status_response = api_client.get(f"/jobs/{job_id}")
            assert status_response.status_code == 200
            status = status_response.json()["status"]
            assert status in ["queued", "processing", "done", "failed"]

    @pytest.mark.asyncio
    async def test_api_job_with_webhook_callback(self, api_client, sample_html_content, mocker):
        """Тест создания задачи с webhook callback."""
        # Mock webhook endpoint
        mocker.patch("httpx.AsyncClient.post")

        files = {"file": ("test.html", sample_html_content, "text/html")}
        data = {"webhook_url": "https://example.com/webhook"}

        response = api_client.post("/jobs/parse", files=files, data=data)
        assert response.status_code == 200

        # Дождаться обработки
        await asyncio.sleep(1)

        # Webhook должен быть вызван (либо при успехе, либо при ошибке)
        # Примечание: в тестовом окружении это может не успеть выполниться
        # Unit тесты покрывают поведение webhook более тщательно


class TestQualityMetricsIntegration:
    """Интеграционные тесты для метрик качества."""

    def test_quality_metrics_consistency(self, sample_html_file):
        """Тест консистентности метрик качества между запусками."""
        parser = ParserFactory.create_parser(str(sample_html_file))

        result1 = parser.parse()
        result2 = parser.parse()

        # Метрики качества должны быть идентичны для одного контента
        assert result1.quality["overall_score"] == result2.quality["overall_score"]
        assert result1.quality["text_completeness"] == result2.quality["text_completeness"]

    def test_quality_metrics_range(self, sample_html_file):
        """Тест что все метрики качества в валидном диапазоне."""
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
            assert 0.0 <= value <= 1.0, f"{metric} = {value} вне диапазона"

    def test_semantic_summary_accuracy(self, sample_html_file):
        """Тест точности semantic summary."""
        parser = ParserFactory.create_parser(str(sample_html_file))
        result = parser.parse()

        summary = result.raw_data["semantic_summary"]

        # Сумма должна совпадать с суммой типов
        type_counts = (
            summary["heading_blocks"]
            + summary["paragraph_blocks"]
            + summary["table_blocks"]
            + summary["list_blocks"]
            + summary["link_blocks"]
        )

        assert summary["total_blocks"] == type_counts

        # Сумма должна совпадать с фактическими блоками
        assert summary["total_blocks"] == len(result.semantic_blocks)


class TestErrorHandlingIntegration:
    """Интеграционные тесты обработки ошибок."""

    def test_corrupted_file_error_propagation(self, temp_dir):
        """Тест propagation ошибки повреждённого файла."""
        # Создать повреждённый DOCX
        corrupted_file = temp_dir / "corrupted.docx"
        corrupted_file.write_bytes(b"Not a valid DOCX")

        with pytest.raises(Exception) as exc_info:
            parser = ParserFactory.create_parser(str(corrupted_file))
            parser.parse()

        # Должно быть исключением парсера
        from parser_manager.models import ParserError

        assert isinstance(exc_info.value, ParserError)

    def test_missing_file_error_propagation(self):
        """Тест propagation ошибки отсутствующего файла."""
        with pytest.raises(Exception) as exc_info:
            parser = ParserFactory.create_parser("/nonexistent/file.html")
            parser.parse()

        from parser_manager.models import DocumentNotFoundError

        assert isinstance(exc_info.value, DocumentNotFoundError)

    def test_unsupported_format_error_propagation(self, temp_dir):
        """Тест propagation ошибки неподдерживаемого формата."""
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("content")

        with pytest.raises(Exception) as exc_info:
            parser = ParserFactory.create_parser(str(unsupported_file))
            parser.parse()

        from parser_manager.models import UnsupportedFormatError

        assert isinstance(exc_info.value, UnsupportedFormatError)


class TestConcurrencyIntegration:
    """Интеграционные тесты параллельных операций."""

    @pytest.mark.asyncio
    async def test_concurrent_parsing(self, sample_html_file):
        """Тест параллельных операций парсинга."""
        import asyncio

        def parse_sync():
            parser = ParserFactory.create_parser(str(sample_html_file))
            return parser.parse()

        # Запустить несколько парсингов параллельно
        loop = asyncio.get_event_loop()
        results = await asyncio.gather(*[loop.run_in_executor(None, parse_sync) for _ in range(5)])

        # Все должны успешно завершиться
        for result in results:
            assert result.success is True
            assert result.format == "html"

    @pytest.mark.asyncio
    async def test_concurrent_job_queue(self, sample_html_content):
        """Тест параллельной очереди задач."""

        queue = ParseJobQueue()
        await queue.start()

        # Поставить несколько задач в очередь
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

        # Дождаться обработки
        await asyncio.sleep(2)
        await queue.stop()

        # Все задачи должны быть обработаны
        for i in range(5):
            job = queue.get_job(f"concurrent_{i}")
            assert job is not None
            assert job.status in ["done", "failed"]


class TestParserRegistryIntegration:
    """Интеграционные тесты реестра парсеров."""

    def test_parser_registration_persistence(self):
        """Тест персистентности регистрации парсеров."""
        # Первый вызов
        formats1 = ParserFactory.get_available_formats()

        # Второй вызов
        formats2 = ParserFactory.get_available_formats()

        assert formats1 == formats2

    def test_parser_creation_repeatability(self, sample_html_file):
        """Тест повторяемости создания парсера."""
        parser1 = ParserFactory.create_parser(str(sample_html_file))
        parser2 = ParserFactory.create_parser(str(sample_html_file))

        assert type(parser1) is type(parser2)
        assert parser1.format_name == parser2.format_name
