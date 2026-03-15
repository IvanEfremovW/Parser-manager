"""Асинхронная очередь задач парсинга."""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from parser_manager.api.service import parse_file_sync


@dataclass
class JobRecord:
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    source_file: str
    temp_file_path: str
    webhook_url: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source_file": self.source_file,
            "webhook_url": self.webhook_url,
            "error": self.error,
        }


class ParseJobQueue:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.jobs: dict[str, JobRecord] = {}
        self._worker_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def enqueue(self, job: JobRecord) -> None:
        self.jobs[job.job_id] = job
        await self.queue.put(job.job_id)

    def get_job(self, job_id: str) -> JobRecord | None:
        return self.jobs.get(job_id)

    async def _worker_loop(self) -> None:
        while True:
            job_id = await self.queue.get()
            job = self.jobs.get(job_id)
            if not job:
                self.queue.task_done()
                continue

            job.status = "processing"
            job.updated_at = datetime.utcnow()

            try:
                result = await asyncio.to_thread(parse_file_sync, job.temp_file_path)
                job.result = result
                job.status = "done"
                job.updated_at = datetime.utcnow()
                await self._send_webhook_if_needed(job)
            except Exception as exc:
                job.error = str(exc)
                job.status = "failed"
                job.updated_at = datetime.utcnow()
                await self._send_webhook_if_needed(job)
            finally:
                try:
                    if os.path.exists(job.temp_file_path):
                        os.remove(job.temp_file_path)
                except OSError:
                    pass
                self.queue.task_done()

    async def _send_webhook_if_needed(self, job: JobRecord) -> None:
        if not job.webhook_url:
            return

        payload: dict[str, Any] = {
            "job_id": job.job_id,
            "status": job.status,
            "source_file": job.source_file,
            "updated_at": job.updated_at.isoformat(),
        }
        if job.status == "done":
            payload["result"] = job.result
        if job.error:
            payload["error"] = job.error

        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(job.webhook_url, json=payload)


job_queue = ParseJobQueue()
