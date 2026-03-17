"""
backend/app/cloud.py — notebooklm-py wrapper (the Studio Engine).

Wraps the ``notebooklm-py`` library to provide:
  - Batch uploader: merges multiple Markdown files into 50-source chunks
  - Artifact manager: generates and downloads mind maps
  - Audio overview generation
  - Slide generation helpers
"""

from __future__ import annotations

import asyncio
import logging
import math
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Maximum sources NotebookLM accepts per notebook
_MAX_SOURCES = 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _chunk_paths(paths: list[Path], chunk_size: int = _MAX_SOURCES) -> list[list[Path]]:
    """Split a list of paths into chunks of at most ``chunk_size``."""
    return [paths[i : i + chunk_size] for i in range(0, len(paths), chunk_size)]


# ---------------------------------------------------------------------------
# NotebookLM client factory
# ---------------------------------------------------------------------------


def _get_client(cookies_path: Path) -> "notebooklm.Client":  # type: ignore[name-defined]
    """
    Instantiate a notebooklm-py client using the saved Playwright cookies.

    Raises ImportError if notebooklm-py is not installed.
    """
    try:
        import notebooklm  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "notebooklm-py is required for cloud features. "
            "Install it with: pip install notebooklm-py"
        ) from exc

    return notebooklm.Client.from_cookie_file(str(cookies_path))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def batch_upload(
    markdown_files: list[Path],
    notebook_title: str,
    cookies_path: Path,
) -> list[str]:
    """
    Upload Markdown files to NotebookLM in batches of up to 50 sources.

    Returns a list of created notebook IDs.
    """
    client = _get_client(cookies_path)
    chunks = _chunk_paths(markdown_files)
    notebook_ids: list[str] = []

    for idx, chunk in enumerate(chunks, 1):
        title = notebook_title if len(chunks) == 1 else f"{notebook_title} — Part {idx}"
        logger.info("Creating notebook '%s' with %d sources…", title, len(chunk))

        notebook = await asyncio.to_thread(
            client.notebooks.create,
            title=title,
            sources=[str(p) for p in chunk],
        )
        notebook_ids.append(notebook.id)
        logger.info("Created notebook %s", notebook.id)

    return notebook_ids


async def generate_mind_map(
    notebook_id: str,
    cookies_path: Path,
) -> dict[str, Any]:
    """
    Trigger mind-map generation for a notebook and return the JSON payload.

    The JSON can be passed directly to the React ``MindMap`` component.
    """
    client = _get_client(cookies_path)

    logger.info("Generating mind map for notebook %s…", notebook_id)
    artifact = await asyncio.to_thread(
        client.artifacts.generate_mind_map,
        notebook_id=notebook_id,
    )

    mind_map_data = await asyncio.to_thread(
        client.artifacts.download_mind_map,
        artifact_id=artifact.id,
    )

    return mind_map_data  # type: ignore[return-value]


async def generate_audio_overview(
    notebook_id: str,
    cookies_path: Path,
    output_path: Path,
) -> Path:
    """
    Generate an Audio Overview for the notebook and save it as an MP3.

    Returns the path to the saved MP3 file.
    """
    client = _get_client(cookies_path)

    logger.info("Generating audio overview for notebook %s…", notebook_id)
    artifact = await asyncio.to_thread(
        client.artifacts.generate_audio_overview,
        notebook_id=notebook_id,
    )

    audio_bytes = await asyncio.to_thread(
        client.artifacts.download_audio,
        artifact_id=artifact.id,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio_bytes)
    logger.info("Audio overview saved to %s", output_path)
    return output_path


async def generate_slides(
    notebook_id: str,
    cookies_path: Path,
) -> list[dict[str, Any]]:
    """
    Generate presentation slides for the notebook.

    Returns a list of slide dicts (title + content).
    """
    client = _get_client(cookies_path)

    logger.info("Generating slides for notebook %s…", notebook_id)
    artifact = await asyncio.to_thread(
        client.artifacts.generate_slides,
        notebook_id=notebook_id,
    )

    slides = await asyncio.to_thread(
        client.artifacts.download_slides,
        artifact_id=artifact.id,
    )

    return slides  # type: ignore[return-value]


async def revise_slide(
    notebook_id: str,
    artifact_id: str,
    slide_index: int,
    revision_prompt: str,
    cookies_path: Path,
) -> dict[str, Any]:
    """
    Send a revision prompt for a specific slide.

    Returns the updated slide dict.
    """
    client = _get_client(cookies_path)

    updated = await asyncio.to_thread(
        client.artifacts.revise_slide,
        notebook_id=notebook_id,
        artifact_id=artifact_id,
        slide_index=slide_index,
        prompt=revision_prompt,
    )

    return updated  # type: ignore[return-value]
