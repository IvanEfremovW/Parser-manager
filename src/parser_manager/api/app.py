"""REST API для Parser Manager с async jobs и webhook callbacks."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from parser_manager.api.jobs import JobRecord, job_queue
from parser_manager.api.service import save_upload_to_temp


app = FastAPI(title="Parser Manager API", version="0.1.0")


@app.on_event("startup")
async def _on_startup() -> None:
    await job_queue.start()


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    await job_queue.stop()


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "queue_size": job_queue.queue.qsize(),
        "jobs_total": len(job_queue.jobs),
    }


@app.post("/jobs/parse")
async def create_parse_job(
    file: UploadFile = File(...),
    webhook_url: str | None = Form(default=None),
):
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


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@app.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str):
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


def run_api() -> None:
    import uvicorn

    uvicorn.run("parser_manager.api.app:app", host="0.0.0.0", port=8000, reload=False)
