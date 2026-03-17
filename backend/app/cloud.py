"""
backend/app/cloud.py — notebooklm-py wrapper for real NotebookLM mode.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

_MAX_SOURCES = 50
_MAX_TEXT_SOURCE_CHARS = 500_000
_DEFAULT_CLIENT_TIMEOUT_SECONDS = float(os.environ.get("BYEGPT_NOTEBOOKLM_TIMEOUT_SECONDS", "90"))
_DEFAULT_ADD_SOURCE_ATTEMPTS = max(
    1,
    int(os.environ.get("BYEGPT_NOTEBOOKLM_ADD_SOURCE_ATTEMPTS", "3")),
)
_ADD_SOURCE_RETRY_BASE_DELAY_SECONDS = float(
    os.environ.get("BYEGPT_NOTEBOOKLM_ADD_SOURCE_RETRY_DELAY_SECONDS", "2")
)
T = TypeVar("T")


class NotebookUploadError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _chunk_items(items: list[T], chunk_size: int = _MAX_SOURCES) -> list[list[T]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def _split_markdown_text(content: str, max_chars: int = _MAX_TEXT_SOURCE_CHARS) -> list[str]:
    if len(content) <= max_chars:
        return [content]

    parts: list[str] = []
    remaining = content
    while remaining:
        if len(remaining) <= max_chars:
            parts.append(remaining)
            break

        split_at = remaining.rfind("\n\n", 0, max_chars)
        if split_at < max_chars // 2:
            split_at = remaining.rfind("\n", 0, max_chars)
        if split_at < max_chars // 2:
            split_at = max_chars

        part = remaining[:split_at].strip()
        if part:
            parts.append(part)
        remaining = remaining[split_at:].lstrip()

    return parts


def _prepare_text_sources(markdown_files: list[Path]) -> list[tuple[str, str]]:
    sources: list[tuple[str, str]] = []
    for path in markdown_files:
        title_base = path.stem.replace("_", " ").strip() or path.name
        markdown = path.read_text(encoding="utf-8", errors="replace")
        parts = _split_markdown_text(markdown)

        for index, part in enumerate(parts, start=1):
            title = title_base if len(parts) == 1 else f"{title_base} ({index}/{len(parts)})"
            sources.append((title[:200], part))

    return sources


async def _get_client(cookies_path: Path):
    try:
        from notebooklm import NotebookLMClient  # type: ignore[import]
    except ImportError as exc:  # pragma: no cover - dependency issue
        raise ImportError(
            "notebooklm-py is required for cloud features. Install it with: pip install notebooklm-py"
        ) from exc

    return await NotebookLMClient.from_storage(
        str(cookies_path),
        timeout=_DEFAULT_CLIENT_TIMEOUT_SECONDS,
    )


def _is_retryable_add_source_error(exc: Exception) -> bool:
    try:
        from notebooklm.exceptions import NetworkError, RPCTimeoutError, SourceAddError  # type: ignore[import]
    except ImportError:  # pragma: no cover - dependency issue
        return False

    if isinstance(exc, RPCTimeoutError | NetworkError):
        return True

    if isinstance(exc, SourceAddError):
        cause = getattr(exc, "cause", None)
        return isinstance(cause, RPCTimeoutError | NetworkError)

    return False


def _build_upload_error(exc: Exception, *, source_title: str) -> NotebookUploadError:
    if _is_retryable_add_source_error(exc):
        return NotebookUploadError(
            f"NotebookLM timed out while adding source '{source_title}'. Try the upload again.",
            status_code=504,
        )

    return NotebookUploadError(
        f"NotebookLM failed while adding source '{source_title}': {exc}",
        status_code=502,
    )


async def _add_text_source_with_retry(
    client: Any,
    notebook_id: str,
    source_title: str,
    markdown: str,
) -> None:
    last_error: Exception | None = None

    for attempt in range(1, _DEFAULT_ADD_SOURCE_ATTEMPTS + 1):
        try:
            await client.sources.add_text(
                notebook_id,
                title=source_title,
                content=markdown,
                wait=True,
            )
            return
        except Exception as exc:
            last_error = exc
            retryable = _is_retryable_add_source_error(exc)
            if not retryable or attempt >= _DEFAULT_ADD_SOURCE_ATTEMPTS:
                break

            delay_seconds = _ADD_SOURCE_RETRY_BASE_DELAY_SECONDS * attempt
            logger.warning(
                "Retrying NotebookLM source upload for '%s' after attempt %d/%d failed: %s",
                source_title,
                attempt,
                _DEFAULT_ADD_SOURCE_ATTEMPTS,
                exc,
            )
            await asyncio.sleep(delay_seconds)

    assert last_error is not None  # pragma: no cover - loop always sets this on failure
    raise _build_upload_error(last_error, source_title=source_title) from last_error


async def batch_upload(
    markdown_files: list[Path],
    notebook_title: str,
    cookies_path: Path,
) -> list[str]:
    notebook_ids: list[str] = []
    text_sources = _prepare_text_sources(markdown_files)
    chunks = _chunk_items(text_sources)

    client = await _get_client(cookies_path)
    async with client:
        for index, chunk in enumerate(chunks, start=1):
            title = notebook_title if len(chunks) == 1 else f"{notebook_title} — Part {index}"
            logger.info("Creating notebook '%s' with %d sources", title, len(chunk))
            notebook = await client.notebooks.create(title)

            for source_title, markdown in chunk:
                await _add_text_source_with_retry(client, notebook.id, source_title, markdown)

            notebook_ids.append(notebook.id)
            logger.info("Created notebook %s", notebook.id)

    return notebook_ids


async def generate_mind_map(
    notebook_id: str,
    cookies_path: Path,
) -> dict[str, Any]:
    client = await _get_client(cookies_path)
    async with client:
        result = await client.artifacts.generate_mind_map(notebook_id=notebook_id)
        note_id = result.get("note_id")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            await client.artifacts.download_mind_map(
                notebook_id=notebook_id,
                artifact_id=note_id,
                output_path=str(tmp_path),
            )
            data = json.loads(tmp_path.read_text(encoding="utf-8"))
        finally:
            tmp_path.unlink(missing_ok=True)

        return {
            "artifact_id": note_id,
            "data": data,
        }


async def generate_audio_overview(
    notebook_id: str,
    cookies_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    client = await _get_client(cookies_path)
    async with client:
        status = await client.artifacts.generate_audio(notebook_id=notebook_id)
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        artifact = await _latest_artifact(client, notebook_id, "audio")

        if output_path is None:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                output_path = Path(tmp.name)
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        await client.artifacts.download_audio(
            notebook_id=notebook_id,
            artifact_id=artifact.id,
            output_path=str(output_path),
        )
        audio_bytes = output_path.read_bytes()

        return {
            "artifact_id": artifact.id,
            "bytes": audio_bytes,
        }


async def generate_slides(
    notebook_id: str,
    cookies_path: Path,
) -> dict[str, Any]:
    client = await _get_client(cookies_path)
    async with client:
        status = await client.artifacts.generate_slide_deck(notebook_id=notebook_id)
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        artifact = await _latest_artifact(client, notebook_id, "slide_deck")

        slides = [
            {
                "title": artifact.title or "Slide deck generated",
                "content": "Slide deck generated in NotebookLM. Use PPTX or PDF export for full content.",
            }
        ]

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as pptx_tmp:
            pptx_path = Path(pptx_tmp.name)
        try:
            await client.artifacts.download_slide_deck(
                notebook_id=notebook_id,
                artifact_id=artifact.id,
                output_path=str(pptx_path),
                output_format="pptx",
            )
            pptx_bytes = pptx_path.read_bytes()
        finally:
            pptx_path.unlink(missing_ok=True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_tmp:
            pdf_path = Path(pdf_tmp.name)
        try:
            await client.artifacts.download_slide_deck(
                notebook_id=notebook_id,
                artifact_id=artifact.id,
                output_path=str(pdf_path),
                output_format="pdf",
            )
            pdf_bytes = pdf_path.read_bytes()
        finally:
            pdf_path.unlink(missing_ok=True)

        return {
            "artifact_id": artifact.id,
            "slides": slides,
            "pptx_bytes": pptx_bytes,
            "pdf_bytes": pdf_bytes,
            "title": artifact.title,
        }


async def generate_quiz(
    notebook_id: str,
    cookies_path: Path,
) -> dict[str, Any]:
    client = await _get_client(cookies_path)
    async with client:
        status = await client.artifacts.generate_quiz(notebook_id=notebook_id)
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        artifact = await _latest_artifact(client, notebook_id, "quiz")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as json_tmp:
            json_path = Path(json_tmp.name)
        try:
            await client.artifacts.download_quiz(
                notebook_id=notebook_id,
                artifact_id=artifact.id,
                output_path=str(json_path),
                output_format="json",
            )
            quiz = json.loads(json_path.read_text(encoding="utf-8"))
        finally:
            json_path.unlink(missing_ok=True)

        return {
            "artifact_id": artifact.id,
            "quiz": quiz,
        }


async def revise_slide(
    notebook_id: str,
    artifact_id: str,
    slide_index: int,
    revision_prompt: str,
    cookies_path: Path,
) -> dict[str, Any]:
    client = await _get_client(cookies_path)
    async with client:
        status = await client.artifacts.revise_slide(
            notebook_id=notebook_id,
            artifact_id=artifact_id,
            slide_index=slide_index,
            prompt=revision_prompt,
        )
        if getattr(status, "task_id", ""):
            await client.artifacts.wait_for_completion(notebook_id, status.task_id)

    return {
        "title": f"Slide {slide_index + 1}",
        "content": f"Revision submitted to NotebookLM: {revision_prompt}",
    }


async def _latest_artifact(client, notebook_id: str, kind: str):
    mapping = {
        "audio": client.artifacts.list_audio,
        "slide_deck": client.artifacts.list_slide_decks,
        "quiz": client.artifacts.list_quizzes,
    }
    artifacts = await mapping[kind](notebook_id)
    completed = [artifact for artifact in artifacts if artifact.is_completed]
    if not completed:
        raise RuntimeError(f"No completed {kind} artifact found for notebook {notebook_id}.")
    completed.sort(key=lambda artifact: artifact.created_at.timestamp() if artifact.created_at else 0, reverse=True)
    return completed[0]
