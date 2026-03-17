"""
core/persona.py — thin wrapper around the existing byegpt persona logic.

Exposes ``build_passport`` so it can be called from the FastAPI backend
without coupling to the Typer CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from byegpt.persona import generate_persona  # noqa: E402
from byegpt.parser import load_conversations  # noqa: E402


def build_passport(
    input_path: Path,
) -> str:
    """
    Generate a Digital Passport Markdown document from a ChatGPT export.

    Parameters
    ----------
    input_path:
        Path to the ChatGPT ``.zip`` export or ``conversations.json`` file.

    Returns
    -------
    str
        Markdown content of the Digital Passport.
    """
    input_path = Path(input_path)
    conversations, zf = load_conversations(input_path)
    if zf is not None:
        zf.close()
    return generate_persona(conversations)
