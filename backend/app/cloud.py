"""
backend/app/cloud.py — notebooklm-py wrapper for real NotebookLM mode.
"""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MAX_SOURCES = 50


def _chunk_paths(paths: list[Path], chunk_size: int = _MAX_SOURCES) -> list[list[Path]]:
    return [paths[index : index + chunk_size] for index in range(0, len(paths), chunk_size)]


async def _get_client(cookies_path: Path):
    try:
        from notebooklm import NotebookLMClient  # type: ignore[import]
    except ImportError as exc:  # pragma: no cover - dependency issue
        raise ImportError(
            "notebooklm-py is required for cloud features. Install it with: pip install notebooklm-py"
        ) from exc

    return await NotebookLMClient.from_storage(str(cookies_path))


async def batch_upload(
    markdown_files: list[Path],
    notebook_title: str,
    cookies_path: Path,
) -> list[str]:
    notebook_ids: list[str] = []
    chunks = _chunk_paths(markdown_files)

    client = await _get_client(cookies_path)
    async with client:
        for index, chunk in enumerate(chunks, start=1):
            title = notebook_title if len(chunks) == 1 else f"{notebook_title} — Part {index}"
            logger.info("Creating notebook '%s' with %d sources", title, len(chunk))
            notebook = await client.notebooks.create(title)

            for path in chunk:
                await client.sources.add_file(notebook.id, path, wait=True)

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
