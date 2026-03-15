"""REST API для Parser Manager с async jobs и webhook callbacks."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from parser_manager.api.jobs import JobRecord, job_queue
from parser_manager.api.service import export_file_sync, save_upload_to_temp


app = FastAPI(
    title="Parser Manager API",
    version="0.2.0",
    description="Унифицированный парсинг HTML/PDF/DOCX/DOC/DJVU → JSON/Markdown/AST",
)


@app.on_event("startup")
async def _on_startup() -> None:
    await job_queue.start()


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    await job_queue.stop()


@app.get("/", tags=["info"])
async def service_info() -> dict:
    """Описание всех возможностей сервиса."""
    return {
        "service": "Parser Manager API",
        "version": "0.2.0",
        "formats_supported": [".html", ".htm", ".pdf", ".docx", ".doc", ".djvu"],
        "export_formats": ["json", "md"],
        "features": [
            "semantic_blocks  — унифицированные смысловые блоки (heading/paragraph/table/list/link)",
            "quality          — оценка качества текста (completeness, noise, broken chars)",
            "file_metrics     — размер файла, длина текста, статистика блоков",
            "doc_stats        — word_count, paragraph_count, reading_time и др.",
            "ast              — дерево документа Document→Section→leaf",
            "export           — вывод в JSON или Markdown",
            "async_jobs       — файл принимается, парсинг идёт фоново, статус опрашивается",
            "webhooks         — POST-уведомление на указанный URL после завершения",
        ],
        "endpoints": {
            "GET  /": "Эта страница",
            "GET  /health": "Статус сервиса + размер очереди",
            "POST /jobs/parse": "Загрузить файл → получить job_id",
            "GET  /jobs/{id}": "Статус задачи",
            "GET  /jobs/{id}/result": "Полный результат (JSON) после завершения",
            "GET  /jobs/{id}/stats": "Только doc_stats задачи",
            "GET  /jobs/{id}/ast": "Только Document AST задачи",
            "GET  /jobs/{id}/export/{fmt}": "Экспорт результата в json или md",
        },
    }


@app.get("/health", tags=["info"])
async def health() -> dict:
    return {
        "status": "ok",
        "queue_size": job_queue.queue.qsize(),
        "jobs_total": len(job_queue.jobs),
    }


@app.post("/jobs/parse", tags=["jobs"])
async def create_parse_job(
    file: UploadFile = File(...),
    webhook_url: str | None = Form(default=None),
):
    """Загрузить файл на парсинг. Возвращает job_id для отслеживания."""
    content = await file.read()
    suffix = Path(file.filename or "").suffix.lower() or ".bin"
    temp_path = save_upload_to_temp(content, suffix=suffix)

    job_id = uuid4().hex
    now = datetime.utcnow()
    job = JobRecord(
        job_id=job_id,
        status="queued",
        created_at=now,
        updated_at=now,
        source_file=file.filename or temp_path.name,
        temp_file_path=str(temp_path),
        webhook_url=webhook_url,
    )
    await job_queue.enqueue(job)

    return {"job_id": job_id, "status": job.status}


@app.get("/jobs/{job_id}", tags=["jobs"])
async def get_job_status(job_id: str):
    """Получить статус задачи."""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@app.get("/jobs/{job_id}/result", tags=["jobs"])
async def get_job_result(job_id: str):
    """Полный результат парсинга в JSON (включает doc_stats, ast, semantic_blocks и др.)"""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in {"queued", "processing"}:
        return JSONResponse(
            status_code=202, content={"job_id": job_id, "status": job.status}
        )
    if job.status == "failed":
        raise HTTPException(status_code=500, detail=job.error or "Parsing failed")

    return {
        "job_id": job_id,
        "status": job.status,
        "source_file": job.source_file,
        "result": job.result,
    }


@app.get("/jobs/{job_id}/stats", tags=["jobs"])
async def get_job_stats(job_id: str):
    """Быстрый доступ к doc_stats задачи: word_count, reading_time и др."""
    job = _require_done_job(job_id)
    result = job.result or {}
    return {
        "job_id": job_id,
        "source_file": job.source_file,
        "doc_stats": result.get("doc_stats", {}),
    }


@app.get("/jobs/{job_id}/ast", tags=["jobs"])
async def get_job_ast(job_id: str):
    """Document AST — дерево документа (Document→Section→leaf)."""
    job = _require_done_job(job_id)
    result = job.result or {}
    return {
        "job_id": job_id,
        "source_file": job.source_file,
        "ast": result.get("ast", {}),
    }


@app.get("/jobs/{job_id}/export/{fmt}", tags=["jobs"])
async def export_job_result(job_id: str, fmt: str):
    """Экспортировать результат задачи в нужный формат: json или md."""
    if fmt not in {"json", "md"}:
        raise HTTPException(status_code=400, detail="Поддерживаемые форматы: json, md")

    job = _require_done_job(job_id)
    result = job.result or {}

    try:
        exported = export_file_sync(result, fmt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if fmt == "md":
        return PlainTextResponse(content=exported, media_type="text/markdown")
    return PlainTextResponse(content=exported, media_type="application/json")


# ── helpers ──────────────────────────────────────────────────────────────────


def _require_done_job(job_id: str) -> JobRecord:
    """Получить готовую задачу или бросить HTTP-исключение."""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in {"queued", "processing"}:
        raise HTTPException(
            status_code=202, detail=f"Job {job_id} is still {job.status}"
        )
    if job.status == "failed":
        raise HTTPException(status_code=500, detail=job.error or "Parsing failed")
    return job


def run_api() -> None:
    import uvicorn

    uvicorn.run("parser_manager.api.app:app", host="0.0.0.0", port=8000, reload=False)
