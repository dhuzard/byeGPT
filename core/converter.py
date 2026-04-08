"""
core/converter.py — thin wrapper around the existing byegpt src/ logic.

Exposes a single ``convert_conversations`` function that can be called both
from the original CLI and from the new FastAPI backend without any coupling
to Typer or Rich.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# Add the src directory to the path so we can import the original modules
# when this package is used outside of an installed editable install.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from byegpt.parser import load_conversations, extract_attachments  # noqa: E402
from byegpt.formatter import write_split_files  # noqa: E402


@dataclass
class ConvertResult:
    """Summary returned by :func:`convert_conversations`."""

    created_files: list[Path] = field(default_factory=list)
    attachment_count: int = 0
    conversation_count: int = 0


def convert_conversations(
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
    Convert a ChatGPT export (ZIP or JSON) into Gemini-optimised Markdown files.

    Parameters
    ----------
    input_path:
        Path to the ChatGPT ``.zip`` export or ``conversations.json`` file.
    output_dir:
        Destination folder for the generated Markdown files.
    max_size_mb:
        Maximum size (in MB) of each output file.
    include_thinking:
        Whether to render GPT-5 / O1 thinking blocks.
    include_attachments:
        Whether to extract image attachments to ``output_dir/assets/``.
    topic_tree:
        Optional dict mapping topic names to lists of subtopics, used by the
        interactive organiser feature.
    progress_callback:
        Optional callable that receives the number of conversations processed
        so far (for progress-bar updates).

    Returns
    -------
    ConvertResult
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    conversations, zf = load_conversations(input_path)
    result = ConvertResult(conversation_count=len(conversations))

    attachment_map: dict[str, str] = {}
    if include_attachments and zf is not None:
        attachment_map = extract_attachments(zf, conversations, output_dir)
        result.attachment_count = len(attachment_map)

    created_files = write_split_files(
        conversations=conversations,
        output_dir=output_dir,
        max_size_mb=max_size_mb,
        attachment_map=attachment_map,
        include_thinking=include_thinking,
        progress_callback=progress_callback,
        topic_tree=topic_tree,
    )
    result.created_files = created_files

    if zf is not None:
        zf.close()

    return result
