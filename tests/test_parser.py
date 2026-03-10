"""Tests for the parser module."""

import json
import zipfile
from pathlib import Path

import pytest

from byegpt.parser import load_conversations, build_message_tree, extract_attachments


class TestLoadConversations:
    """Tests for load_conversations()."""

    def test_load_from_json_file(self, tmp_path, sample_conversations):
        """Loading from a plain JSON file returns conversations and no ZipFile."""
        json_file = tmp_path / "conversations.json"
        json_file.write_text(json.dumps(sample_conversations), encoding="utf-8")

        convs, zf = load_conversations(json_file)

        assert zf is None
        assert len(convs) == 3
        assert convs[0]["title"] == "Test Conversation One"

    def test_load_from_zip(self, tmp_path, sample_conversations):
        """Loading from a ZIP file returns conversations and a ZipFile handle."""
        zip_path = tmp_path / "export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("conversations.json", json.dumps(sample_conversations))

        convs, zf = load_conversations(zip_path)

        try:
            assert zf is not None
            assert len(convs) == 3
            assert convs[0]["title"] == "Test Conversation One"
        finally:
            if zf:
                zf.close()

    def test_load_from_zip_missing_json(self, tmp_path):
        """Loading from a ZIP without conversations.json raises FileNotFoundError."""
        zip_path = tmp_path / "bad_export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("other.txt", "hello")

        with pytest.raises(FileNotFoundError, match="conversations.json"):
            load_conversations(zip_path)


class TestBuildMessageTree:
    """Tests for build_message_tree()."""

    def test_ordering(self, single_conversation):
        """Messages are returned in chronological tree order."""
        mapping = single_conversation["mapping"]
        ordered = build_message_tree(mapping)

        # Should follow root → msg-1 → msg-2 → ... → msg-8
        assert len(ordered) == 9  # root + 8 messages
        assert ordered[0]["id"] == "root"
        assert ordered[1]["id"] == "msg-1"
        assert ordered[-1]["id"] == "msg-8"

    def test_empty_mapping(self):
        """Empty mapping returns empty list."""
        assert build_message_tree({}) == []

    def test_single_root_no_children(self):
        """A single root with no children returns just the root."""
        mapping = {
            "root": {"id": "root", "message": None, "parent": None, "children": []}
        }
        result = build_message_tree(mapping)
        assert len(result) == 1


class TestExtractAttachments:
    """Tests for extract_attachments()."""

    def test_extracts_matching_files(self, tmp_path, sample_conversations):
        """Attachments referenced in conversations are extracted from the ZIP."""
        zip_path = tmp_path / "export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("conversations.json", json.dumps(sample_conversations))
            # Add a file matching the asset_pointer in the fixture
            zf.writestr("file_abc123-sanitized.png", b"fake image data")

        output_dir = tmp_path / "output"

        with zipfile.ZipFile(zip_path, "r") as zf:
            result = extract_attachments(zf, sample_conversations, output_dir)

        assert "file_abc123" in result
        assert result["file_abc123"].startswith("assets/")
        assert (output_dir / result["file_abc123"]).exists()

    def test_no_zip_returns_empty(self, sample_conversations, tmp_path):
        """When no ZipFile is provided, returns an empty mapping."""
        result = extract_attachments(None, sample_conversations, tmp_path)
        assert result == {}

    def test_missing_file_in_zip_skipped(self, tmp_path, sample_conversations):
        """Files referenced but not in the ZIP are silently skipped."""
        zip_path = tmp_path / "export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("conversations.json", json.dumps(sample_conversations))
            # Deliberately don't add file_abc123

        output_dir = tmp_path / "output"

        with zipfile.ZipFile(zip_path, "r") as zf:
            result = extract_attachments(zf, sample_conversations, output_dir)

        assert "file_abc123" not in result
