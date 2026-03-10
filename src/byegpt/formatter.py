"""
Formatter module — converts parsed ChatGPT conversations to
Gemini-optimized Markdown with frontmatter, callouts, and attachments.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from byegpt.parser import build_message_tree


# ---------------------------------------------------------------------------
# Content-type handlers
# ---------------------------------------------------------------------------

# Content types to silently skip (noise for the final Markdown)
_SKIP_TYPES = frozenset({
    "system_error",
    "tether_browsing_display",
    "sonic_webpage",
    "user_editable_context",
    "computer_output",
})


def _format_text_message(
    role: str,
    parts: list[Any],
    attachment_map: dict[str, str],
) -> str:
    """Format a standard text or multimodal_text message."""
    chunks: list[str] = []

    for part in parts:
        if isinstance(part, str):
            chunks.append(part)
        elif isinstance(part, dict):
            ct = part.get("content_type", "")
            if ct == "image_asset_pointer":
                pointer = part.get("asset_pointer", "")
                file_id = pointer.replace("sediment://", "")
                rel_path = attachment_map.get(file_id)
                if rel_path:
                    chunks.append(f"\n![Image]({rel_path})\n")
                else:
                    chunks.append("\n*[Image not available]*\n")

    text = "".join(chunks).strip()
    if not text:
        return ""

    role_name = "USER" if role == "user" else "ASSISTANT"
    return f"**{role_name}:**\n{text}\n\n"


def _format_thinking_block(content: dict[str, Any]) -> str:
    """Format a thinking/thoughts block as a collapsed Obsidian callout."""
    thoughts = content.get("thoughts", "")
    # Some exports store thoughts as a list
    if isinstance(thoughts, list):
        thoughts = "\n".join(str(t) for t in thoughts)
    thoughts = str(thoughts).strip()
    if not thoughts:
        return ""

    # Indent every line for the callout block
    indented = "\n".join(f"> {line}" for line in thoughts.splitlines())
    return f"> [!abstract]- 💭 Thinking Process\n{indented}\n\n"


def _format_reasoning_recap(content: dict[str, Any]) -> str:
    """Format a reasoning_recap block as a collapsed Obsidian callout."""
    recap_content = content.get("content", "")
    if isinstance(recap_content, list):
        recap_content = "\n".join(str(c) for c in recap_content)
    recap_content = str(recap_content).strip()
    if not recap_content:
        # Try parts as fallback
        parts = content.get("parts", [])
        recap_content = "".join(p for p in parts if isinstance(p, str)).strip()
    if not recap_content:
        return ""

    indented = "\n".join(f"> {line}" for line in recap_content.splitlines())
    return f"> [!info]- 📋 Reasoning Summary\n{indented}\n\n"


def _format_code_block(content: dict[str, Any]) -> str:
    """Format a code content block."""
    parts = content.get("parts", [])
    text = "".join(p for p in parts if isinstance(p, str)).strip()
    if not text:
        return ""
    # Try to detect language from the text content
    lang = content.get("language", "")
    return f"```{lang}\n{text}\n```\n\n"


def _format_execution_output(content: dict[str, Any]) -> str:
    """Format execution output as a code block."""
    parts = content.get("parts", [])
    text = "".join(p for p in parts if isinstance(p, str)).strip()
    if not text:
        return ""
    return f"**Output:**\n```\n{text}\n```\n\n"


def _format_tether_quote(content: dict[str, Any]) -> str:
    """Format a tether_quote (web citation) as a blockquote."""
    parts = content.get("parts", [])
    text = "".join(p for p in parts if isinstance(p, str)).strip()
    if not text:
        return ""
    quoted = "\n".join(f"> {line}" for line in text.splitlines())
    return f"{quoted}\n\n"


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------

def format_message(
    node: dict[str, Any],
    attachment_map: dict[str, str],
    include_thinking: bool = True,
) -> str | None:
    """
    Format a single message node into Markdown.

    Returns None if the message should be skipped.
    """
    message = node.get("message")
    if not message:
        return None

    content = message.get("content")
    if not content:
        return None

    content_type = content.get("content_type", "text")
    role = message.get("author", {}).get("role", "")

    # Skip system messages and noise
    if role == "system":
        return None
    if content_type in _SKIP_TYPES:
        return None

    # Thinking blocks
    if content_type == "thoughts":
        if not include_thinking:
            return None
        return _format_thinking_block(content) or None

    # Reasoning recap
    if content_type == "reasoning_recap":
        if not include_thinking:
            return None
        return _format_reasoning_recap(content) or None

    # Code blocks
    if content_type == "code":
        return _format_code_block(content) or None

    # Execution output
    if content_type == "execution_output":
        return _format_execution_output(content) or None

    # Tether quote (web citations)
    if content_type == "tether_quote":
        return _format_tether_quote(content) or None

    # Standard text / multimodal_text
    if content_type in ("text", "multimodal_text"):
        parts = content.get("parts", [])
        return _format_text_message(role, parts, attachment_map) or None

    # Unknown content type — skip silently
    return None


# ---------------------------------------------------------------------------
# Conversation formatting
# ---------------------------------------------------------------------------

def _generate_frontmatter(conv: dict[str, Any]) -> str:
    """Generate YAML frontmatter for a conversation."""
    title = conv.get("title") or "Untitled conversation"
    # Escape quotes in title
    safe_title = title.replace('"', '\\"')

    date_raw = conv.get("create_time")
    date_str = (
        datetime.fromtimestamp(date_raw).strftime("%Y-%m-%d")
        if date_raw
        else "unknown"
    )

    # Try to find the model slug from the first assistant message
    model = "unknown"
    mapping = conv.get("mapping", {})
    for node in mapping.values():
        msg = node.get("message")
        if not msg:
            continue
        meta = msg.get("metadata", {})
        slug = meta.get("model_slug", "")
        if slug:
            model = slug
            break

    lines = [
        "---",
        f'title: "{safe_title}"',
        f"date: {date_str}",
        f"model: {model}",
        "tags: [chatgpt-export, archive]",
        "---",
        "",
    ]
    return "\n".join(lines)


def format_conversation(
    conv: dict[str, Any],
    attachment_map: dict[str, str],
    include_thinking: bool = True,
) -> str:
    """Format a full conversation into Markdown with frontmatter."""
    parts: list[str] = []

    # Frontmatter
    parts.append(_generate_frontmatter(conv))

    # Title heading
    title = conv.get("title") or "Untitled conversation"
    date_raw = conv.get("create_time")
    date_str = (
        datetime.fromtimestamp(date_raw).strftime("%Y-%m-%d")
        if date_raw
        else "Unknown date"
    )
    parts.append(f"# {title} ({date_str})\n\n")

    # Messages in tree order
    mapping = conv.get("mapping", {})
    ordered_nodes = build_message_tree(mapping)

    for node in ordered_nodes:
        msg_text = format_message(node, attachment_map, include_thinking)
        if msg_text:
            parts.append(msg_text)

    return "".join(parts)


# ---------------------------------------------------------------------------
# File splitting & writing
# ---------------------------------------------------------------------------

def write_split_files(
    conversations: list[dict[str, Any]],
    output_dir: Path,
    max_size_mb: float = 7.0,
    attachment_map: dict[str, str] | None = None,
    include_thinking: bool = True,
    progress_callback: Any = None,
    topic_tree: dict[str, list[str]] | None = None,
) -> list[Path]:
    """
    Convert all conversations to Markdown, splitting into files that
    respect the size limit (optimized for Gemini's context window).

    If `topic_tree` is provided, conversations will be organized into nested
    folders (topic/subtopic). Returns list of created file paths.
    """
    if attachment_map is None:
        attachment_map = {}

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    max_bytes = int(max_size_mb * 1024 * 1024)
    created_files: list[Path] = []
    
    # State tracking per folder so size limits work independently
    folder_state: dict[str, dict[str, Any]] = {}

    for i, conv in enumerate(conversations):
        # ── Routing Logic ──
        target_path = Path(".")
        title = (conv.get("title") or "").lower()
        
        if topic_tree:
            matched_topic = None
            matched_subtopic = None
            
            # Find top-level topic match
            for topic in topic_tree.keys():
                if topic.lower() in title:
                    matched_topic = topic
                    # Find subtopic match within that topic
                    for sub in topic_tree[topic]:
                        if sub.lower() in title:
                            matched_subtopic = sub
                            break
                    break
            
            if matched_topic:
                target_path = Path(matched_topic)
                if matched_subtopic:
                    target_path = target_path / matched_subtopic
            else:
                target_path = Path("Uncategorized")
        
        folder_key = str(target_path)

        # Initialize folder state if needed
        if folder_key not in folder_state:
            folder_dir = output_dir / target_path
            folder_dir.mkdir(parents=True, exist_ok=True)
            folder_state[folder_key] = {
                "dir": folder_dir,
                "current_content": "",
                "file_idx": 1,
                "depth": len(target_path.parts) if str(target_path) != "." else 0,
            }
            
        state = folder_state[folder_key]
        
        # Adjust attachment paths based on folder depth
        # For each level of depth, we add a '../'
        local_att_map = attachment_map
        if state["depth"] > 0:
            prefix = "../" * state["depth"]
            local_att_map = {k: f"{prefix}{v}" for k, v in attachment_map.items()}

        conv_md = format_conversation(conv, local_att_map, include_thinking)
        conv_md += "\n---\n\n"

        state["current_content"] += conv_md

        # Check size limit
        if len(state["current_content"].encode("utf-8")) > max_bytes:
            # File name includes part of the path to avoid collisions
            safe_name = folder_key.replace(os.sep, "_").replace("/", "_").lower()
            if safe_name == ".": safe_name = "part"
            
            file_path = state["dir"] / f"history_{safe_name}_{state["file_idx"]}.md"
            file_path.write_text(state["current_content"], encoding="utf-8")
            created_files.append(file_path)
            state["file_idx"] += 1
            state["current_content"] = ""

        if progress_callback:
            progress_callback(i + 1)

    # Final flush
    for folder_key, state in folder_state.items():
        if state["current_content"].strip():
            safe_name = folder_key.replace(os.sep, "_").replace("/", "_").lower()
            if safe_name == ".": safe_name = "part"
            
            file_path = state["dir"] / f"history_{safe_name}_{state["file_idx"]}.md"
            file_path.write_text(state["current_content"], encoding="utf-8")
            created_files.append(file_path)

    return created_files
