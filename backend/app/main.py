"""
backend/app/main.py — FastAPI entry point and API routes for byeGPT Studio.

Routes
------
GET  /health                    — Liveness probe
GET  /auth/status               — Is there a saved Google session?
POST /auth/login                — Start a headless login flow
POST /convert                   — Convert a ChatGPT ZIP/JSON export
POST /persona                   — Generate a Digital Passport
POST /notebooks/upload          — Batch-upload Markdown files to NotebookLM
GET  /notebooks/{id}/mindmap    — Generate & return mind-map JSON
GET  /notebooks/{id}/audio      — Generate & return audio overview MP3
GET  /notebooks/{id}/slides     — Generate & return slide list
PATCH /notebooks/{id}/slides/{idx} — Revise a slide with a custom prompt
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .auth_manager import is_authenticated, login_and_save
from .cloud import (
    batch_upload,
    generate_audio_overview,
    generate_mind_map,
    generate_slides,
    revise_slide,
)
from .parser import convert_with_anchors

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="byeGPT Studio API",
    description=(
        "Backend for the byeGPT v3 Studio — converts ChatGPT exports, "
        "manages NotebookLM notebooks, and surfaces AI artifacts."
    ),
    version="3.0.0",
)

# Allow the React dev-server (port 5173) and any production origin to call the API
_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STORAGE_DIR = Path(os.environ.get("BYEGPT_STORAGE", ".byegpt"))
_COOKIES_PATH = _STORAGE_DIR / "storage.json"
_AUDIO_DIR = _STORAGE_DIR / "audio"
_CONVERTED_DIR = _STORAGE_DIR / "converted"
_TUSD_UPLOAD_DIR = Path(os.environ.get("BYEGPT_TUSD_UPLOAD_DIR", ".uploads"))

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class UploadNotebookRequest(BaseModel):
    notebook_title: str = "byeGPT Archive"
    output_dir: str = str(_CONVERTED_DIR)


class ReviseSlideRequest(BaseModel):
    revision_prompt: str
    artifact_id: str


class TusUploadInfo(BaseModel):
    ID: str
    Size: int
    Offset: int
    MetaData: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Liveness probe."""
    return {"status": "ok", "version": "3.0.0"}


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------


@app.get("/auth/status", tags=["auth"])
async def auth_status() -> dict:
    """Return whether a valid Google session cookie exists."""
    authenticated = is_authenticated(_COOKIES_PATH)
    return {"authenticated": authenticated}


@app.post("/auth/login", tags=["auth"])
async def auth_login(background_tasks: BackgroundTasks) -> dict:
    """
    Start a headless Playwright browser so the user can complete Google login.
    The session is saved asynchronously; poll ``/auth/status`` to check progress.
    """
    if is_authenticated(_COOKIES_PATH):
        return {"status": "already_authenticated"}

    if os.name != "nt" and not os.environ.get("DISPLAY"):
        raise HTTPException(
            status_code=501,
            detail=(
                "Interactive NotebookLM login is unavailable in Docker without an X server. "
                "Provide a valid .byegpt/storage.json session file or run the backend outside Docker for login."
            ),
        )

    background_tasks.add_task(login_and_save, _COOKIES_PATH, headless=False)
    return {"status": "login_started", "message": "Open the browser window to complete login."}


# ---------------------------------------------------------------------------
# Conversion routes
# ---------------------------------------------------------------------------


@app.post("/convert", tags=["convert"])
async def convert_export(
    file: UploadFile = File(..., description="ChatGPT .zip or conversations.json export"),
    max_size_mb: float = Form(7.0),
    include_thinking: bool = Form(True),
    include_attachments: bool = Form(True),
) -> dict:
    """
    Convert a ChatGPT export to Gemini-optimised Markdown with Context Anchors.
    """
    suffix = Path(file.filename or "upload").suffix or ".zip"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    output_dir = _CONVERTED_DIR / str(uuid.uuid4())

    try:
        return await _convert_archive(
            input_path=tmp_path,
            output_dir=output_dir,
            max_size_mb=max_size_mb,
            include_thinking=include_thinking,
            include_attachments=include_attachments,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/convert/tus/{upload_id}", tags=["convert"])
async def convert_tus_upload(
    upload_id: str,
    max_size_mb: float = 7.0,
    include_thinking: bool = True,
    include_attachments: bool = True,
) -> dict:
    """Convert a completed tus upload stored on the shared upload volume."""
    info = _load_tus_upload_info(upload_id)
    source_path = _TUSD_UPLOAD_DIR / upload_id
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Tus upload '{upload_id}' not found.")

    file_size = source_path.stat().st_size
    metadata = {key: _normalize_tusd_metadata(value) for key, value in info.MetaData.items()}

    if file_size < info.Size:
        raise HTTPException(status_code=409, detail="Upload is not complete yet.")

    original_name = metadata.get("filename")
    if not original_name:
        raise HTTPException(status_code=400, detail="Tus upload metadata is missing filename.")

    suffix = Path(original_name).suffix.lower()
    if suffix not in {".zip", ".json"}:
        raise HTTPException(status_code=400, detail="Unsupported upload type. Use .zip or .json.")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(source_path.read_bytes())
        tmp_path = Path(tmp.name)

    output_dir = _CONVERTED_DIR / str(uuid.uuid4())

    try:
        return await _convert_archive(
            input_path=tmp_path,
            output_dir=output_dir,
            max_size_mb=max_size_mb,
            include_thinking=include_thinking,
            include_attachments=include_attachments,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/persona", tags=["convert"])
async def generate_passport(
    file: UploadFile = File(..., description="ChatGPT .zip or conversations.json export"),
) -> dict:
    """Generate a Digital Passport from a ChatGPT export."""
    from core.persona import build_passport  # imported lazily to keep startup fast

    suffix = Path(file.filename or "upload").suffix or ".zip"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        markdown = await asyncio.to_thread(build_passport, tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return {"passport_markdown": markdown}


# ---------------------------------------------------------------------------
# NotebookLM routes
# ---------------------------------------------------------------------------


@app.post("/notebooks/upload", tags=["notebooklm"])
async def upload_to_notebooklm(body: UploadNotebookRequest) -> dict:
    """
    Batch-upload converted Markdown files to NotebookLM (up to 50 sources per notebook).
    """
    if not is_authenticated(_COOKIES_PATH):
        raise HTTPException(status_code=401, detail="Not authenticated. Call /auth/login first.")

    output_dir = Path(body.output_dir)
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail=f"Output dir '{output_dir}' not found.")

    md_files = list(output_dir.rglob("*.md"))
    if not md_files:
        raise HTTPException(status_code=404, detail="No Markdown files found in output_dir.")

    notebook_ids = await batch_upload(
        markdown_files=md_files,
        notebook_title=body.notebook_title,
        cookies_path=_COOKIES_PATH,
    )

    return {"notebook_ids": notebook_ids, "source_count": len(md_files)}


@app.get("/notebooks/{notebook_id}/mindmap", tags=["notebooklm"])
async def get_mind_map(notebook_id: str) -> dict:
    """Generate and return a mind-map JSON for the specified notebook."""
    if not is_authenticated(_COOKIES_PATH):
        raise HTTPException(status_code=401, detail="Not authenticated.")

    data = await generate_mind_map(notebook_id=notebook_id, cookies_path=_COOKIES_PATH)
    return {"notebook_id": notebook_id, "mind_map": data}


@app.get("/notebooks/{notebook_id}/audio", tags=["notebooklm"])
async def get_audio_overview(notebook_id: str) -> FileResponse:
    """Generate an Audio Overview MP3 and stream it back to the client."""
    if not is_authenticated(_COOKIES_PATH):
        raise HTTPException(status_code=401, detail="Not authenticated.")

    _AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _AUDIO_DIR / f"{notebook_id}.mp3"

    await generate_audio_overview(
        notebook_id=notebook_id,
        cookies_path=_COOKIES_PATH,
        output_path=output_path,
    )

    return FileResponse(
        path=str(output_path),
        media_type="audio/mpeg",
        filename=f"overview_{notebook_id}.mp3",
    )


@app.get("/notebooks/{notebook_id}/slides", tags=["notebooklm"])
async def get_slides(notebook_id: str) -> dict:
    """Generate and return a list of slides for the specified notebook."""
    if not is_authenticated(_COOKIES_PATH):
        raise HTTPException(status_code=401, detail="Not authenticated.")

    slides = await generate_slides(notebook_id=notebook_id, cookies_path=_COOKIES_PATH)
    return {"notebook_id": notebook_id, "slides": slides}


@app.patch("/notebooks/{notebook_id}/slides/{slide_index}", tags=["notebooklm"])
async def revise_notebook_slide(
    notebook_id: str,
    slide_index: int,
    body: ReviseSlideRequest,
) -> dict:
    """Send a revision prompt for a specific slide and return the updated slide."""
    if not is_authenticated(_COOKIES_PATH):
        raise HTTPException(status_code=401, detail="Not authenticated.")

    updated = await revise_slide(
        notebook_id=notebook_id,
        artifact_id=body.artifact_id,
        slide_index=slide_index,
        revision_prompt=body.revision_prompt,
        cookies_path=_COOKIES_PATH,
    )
    return {"notebook_id": notebook_id, "slide_index": slide_index, "slide": updated}


async def _convert_archive(
    input_path: Path,
    output_dir: Path,
    max_size_mb: float,
    include_thinking: bool,
    include_attachments: bool,
) -> dict:
    try:
        result = await asyncio.to_thread(
            convert_with_anchors,
            input_path=input_path,
            output_dir=output_dir,
            max_size_mb=max_size_mb,
            include_thinking=include_thinking,
            include_attachments=include_attachments,
        )
    except Exception as exc:
        logger.exception("Conversion failed for %s", input_path)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {exc}") from exc

    return {
        "output_dir": str(output_dir),
        "files_created": len(result.created_files),
        "attachment_count": result.attachment_count,
        "conversation_count": result.conversation_count,
        "file_paths": [str(p) for p in result.created_files],
    }


def _load_tus_upload_info(upload_id: str) -> TusUploadInfo:
    info_path = _TUSD_UPLOAD_DIR / f"{upload_id}.info"
    if not info_path.exists():
        raise HTTPException(status_code=404, detail=f"Tus upload '{upload_id}' not found.")

    try:
        payload = json.loads(info_path.read_text(encoding="utf-8"))
        return TusUploadInfo.model_validate(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Tus upload metadata is invalid.") from exc


def _normalize_tusd_metadata(value: str) -> str:
    if not value:
        return value

    try:
        decoded = base64.b64decode(value, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return value

    if decoded and all(ch.isprintable() or ch.isspace() for ch in decoded):
        return decoded
    return value
