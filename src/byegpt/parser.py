"""
Parser module — handles ZIP/JSON loading, attachment extraction,
and message tree reconstruction from ChatGPT exports.
"""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any


def load_conversations(input_path: Path) -> tuple[list[dict[str, Any]], zipfile.ZipFile | None]:
    """
    Load conversations from a ChatGPT export.

    Accepts either a `.zip` file or a `conversations.json` file.

    Returns:
        (conversations_list, zip_handle_or_none)
        Caller is responsible for closing the ZipFile if returned.
    """
    input_path = Path(input_path)

    if input_path.suffix.lower() == ".zip":
        zf = zipfile.ZipFile(input_path, "r")
        try:
            raw = zf.read("conversations.json")
        except KeyError:
            zf.close()
            raise FileNotFoundError(
                "The ZIP file does not contain 'conversations.json'. "
                "Make sure this is a ChatGPT data export."
            )
        data = json.loads(raw)
        return data, zf

    # Plain JSON file
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data, None


def build_message_tree(mapping: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Reconstruct the chronological message order from ChatGPT's mapping dict.

    ChatGPT stores messages in a tree structure with parent/children links.
    This function walks the tree from root to leaves following the *last*
    child at each branch (the "active" conversation path), yielding messages
    in the order they were displayed to the user.
    """
    if not mapping:
        return []

    # Find the root node (no parent, or parent is None)
    root_id = None
    for node_id, node in mapping.items():
        if node.get("parent") is None:
            root_id = node_id
            break

    if root_id is None:
        # Fallback: just iterate in dict order
        return [mapping[nid] for nid in mapping]

    ordered: list[dict[str, Any]] = []
    current_id = root_id

    while current_id is not None:
        node = mapping.get(current_id)
        if node is None:
            break
        ordered.append(node)
        children = node.get("children", [])
        # Follow the last child (active branch)
        current_id = children[-1] if children else None

    return ordered


# ---------------------------------------------------------------------------
# Attachment extraction
# ---------------------------------------------------------------------------

_FILE_ID_PATTERN = re.compile(r"file[-_][0-9a-fA-F]+")


def _find_zip_entry_for_id(file_id: str, zip_names: list[str]) -> str | None:
    """Find the ZIP entry whose name contains the given file ID."""
    for name in zip_names:
        if file_id in name:
            return name
    return None


def _sanitize_filename(name: str) -> str:
    """Create a filesystem-safe filename from a potentially messy zip entry name."""
    # Take only the basename (some exports have nested paths)
    basename = Path(name).name
    # Replace problematic characters
    safe = re.sub(r"[^\w.\-]", "_", basename)
    # Collapse multiple underscores
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe if safe else "unnamed_file"


def extract_attachments(
    zf: zipfile.ZipFile | None,
    conversations: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, str]:
    """
    Extract attachments referenced in conversations from the ZIP archive.

    Scans for:
    - `image_asset_pointer` parts with `sediment://file_xxx` references
    - `metadata.attachments` entries with `id` fields

    Returns:
        Mapping of {file_id: relative_path_from_output_dir} for Markdown links.
    """
    if zf is None:
        return {}

    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    zip_names = zf.namelist()
    file_id_map: dict[str, str] = {}

    # Collect all referenced file IDs
    referenced_ids: set[str] = set()

    for conv in conversations:
        mapping = conv.get("mapping", {})
        for node in mapping.values():
            msg = node.get("message")
            if not msg:
                continue

            # Check content parts for image_asset_pointer
            content = msg.get("content", {})
            for part in content.get("parts", []):
                if isinstance(part, dict):
                    pointer = part.get("asset_pointer", "")
                    if pointer.startswith("sediment://"):
                        file_id = pointer.replace("sediment://", "")
                        referenced_ids.add(file_id)

            # Check metadata attachments
            meta = msg.get("metadata", {})
            for att in meta.get("attachments", []):
                att_id = att.get("id", "")
                if att_id:
                    referenced_ids.add(att_id)

    # Extract each referenced file
    for file_id in referenced_ids:
        zip_entry = _find_zip_entry_for_id(file_id, zip_names)
        if zip_entry is None:
            continue

        safe_name = _sanitize_filename(zip_entry)
        dest_path = assets_dir / safe_name

        # Avoid overwriting (name collisions)
        counter = 1
        original_stem = dest_path.stem
        while dest_path.exists():
            dest_path = assets_dir / f"{original_stem}_{counter}{dest_path.suffix}"
            counter += 1

        # Extract
        with zf.open(zip_entry) as src, open(dest_path, "wb") as dst:
            shutil.copyfileobj(src, dst)

        # Store relative path from the output dir (for Markdown links)
        rel_path = f"assets/{dest_path.name}"
        file_id_map[file_id] = rel_path

    return file_id_map
