"""
core — shared byeGPT logic re-exported for use by both the CLI and the backend.
"""

from .converter import convert_conversations, ConvertResult
from .persona import build_passport

__all__ = ["convert_conversations", "ConvertResult", "build_passport"]
