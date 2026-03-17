"""
backend/app/parser.py — Optimised Markdown conversion for NotebookLM.

Wraps ``core.converter`` and adds "Context Anchors" to the generated
Markdown so Gemini can cite original chat sources properly inside the
NotebookLM UI.

A Context Anchor looks like:

    <!-- source: https://chatgpt.com/c/<conversation_id> -->

or, when no URL is available:

    <!-- source: conversation:<title> -->

These invisible HTML comments are picked up by NotebookLM's citation
engine while staying invisible to human readers.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# Re-export core functions so callers only need to import from this module
# ---------------------------------------------------------------------------

_CORE = Path(__file__).resolve().parent.parent.parent / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.converter import convert_conversations, ConvertResult  # noqa: E402
from byegpt.parser import load_conversations  # noqa: E402


logger = logging.getLogger(__name__)
from byegpt.formatter import format_conversation  # noqa: E402


# ---------------------------------------------------------------------------
# Context Anchor helpers
# ---------------------------------------------------------------------------

_CHATGPT_URL_BASE = "https://chatgpt.com/c/"


def _make_context_anchor(conversation: dict[str, Any]) -> str:
    """Return an HTML comment anchor for the given conversation."""
    conv_id = conversation.get("id", "")
    title = conversation.get("title", "Untitled")

    if conv_id:
        url = f"{_CHATGPT_URL_BASE}{conv_id}"
        return f"<!-- source: {url} -->\n"
    # Fallback when there is no usable ID
    safe_title = re.sub(r"[^\w\s-]", "", title)[:80].strip()
    return f"<!-- source: conversation:{safe_title} -->\n"


def inject_context_anchors(markdown: str, conversation: dict[str, Any]) -> str:
    """
    Prepend a Context Anchor comment to the Markdown output.

    The anchor is placed *before* the YAML front-matter block (if present)
    so it does not interfere with YAML parsing.
    """
    anchor = _make_context_anchor(conversation)
    return anchor + markdown


# ---------------------------------------------------------------------------
# Public conversion function with anchors
# ---------------------------------------------------------------------------


def convert_with_anchors(
    input_path: Path,
    output_dir: Path,
    *,
    max_size_mb: float = 7.0,
    include_thinking: bool = True,
    include_attachments: bool = True,
    topic_tree: Optional[dict[str, list[str]]] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> ConvertResult:
    """
    Convert a ChatGPT export and inject Context Anchors into each file.

    This is a thin wrapper around :func:`core.converter.convert_conversations`
    that post-processes each output file to prepend a ``<!-- source: … -->``
    comment.

    Parameters mirror those of :func:`~core.converter.convert_conversations`.
    """
    result = convert_conversations(
        input_path=input_path,
        output_dir=output_dir,
        max_size_mb=max_size_mb,
        include_thinking=include_thinking,
        include_attachments=include_attachments,
        topic_tree=topic_tree,
        progress_callback=progress_callback,
    )

    # Build a quick lookup: filename stem → conversation id/title
    # (The formatter uses the conversation title as the file stem)
    conversations, zf = load_conversations(input_path)
    if zf is not None:
        zf.close()

    conv_by_title: dict[str, dict[str, Any]] = {
        (c.get("title") or "Untitled"): c for c in conversations
    }

    for md_file in result.created_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            # Match the conversation by scanning the title in the YAML front-matter
            title_match = re.search(r'^title:\s*"?([^"\n]+)"?', content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else ""
            conv = conv_by_title.get(title)
            if conv:
                content = inject_context_anchors(content, conv)
                md_file.write_text(content, encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            # Log but don't crash the whole conversion for a single anchor injection failure
            logger.warning("Failed to inject context anchor into %s", md_file, exc_info=True)

    return result
