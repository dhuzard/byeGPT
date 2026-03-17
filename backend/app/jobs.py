from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._tasks: dict[str, asyncio.Task[Any]] = {}

    def create(
        self,
        *,
        notebook_id: str,
        artifact_types: list[str],
        runner: Callable[[str], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        record = {
            "job_id": job_id,
            "notebook_id": notebook_id,
            "artifact_types": artifact_types,
            "status": "queued",
            "created_at": utcnow_iso(),
            "updated_at": utcnow_iso(),
            "artifact_ids": [],
            "error": None,
            "result": None,
        }
        self._jobs[job_id] = record
        self._tasks[job_id] = asyncio.create_task(self._run(job_id, runner))
        return record

    async def _run(
        self,
        job_id: str,
        runner: Callable[[str], Awaitable[dict[str, Any]]],
    ) -> None:
        record = self._jobs[job_id]
        record["status"] = "running"
        record["updated_at"] = utcnow_iso()
        try:
            result = await runner(job_id)
            record["status"] = "completed"
            record["result"] = result
            record["artifact_ids"] = result.get("artifact_ids", [])
        except Exception as exc:  # pragma: no cover - defensive path
            record["status"] = "failed"
            record["error"] = str(exc)
        finally:
            record["updated_at"] = utcnow_iso()

    def get(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)


jobs = JobRegistry()
