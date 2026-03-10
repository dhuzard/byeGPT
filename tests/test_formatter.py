"""Tests for the formatter module."""

from pathlib import Path

import pytest

from byegpt.formatter import (
    format_message,
    format_conversation,
    write_split_files,
    _generate_frontmatter,
)


class TestFormatMessage:
    """Tests for format_message()."""

    def test_text_message_user(self):
        """User text messages are formatted with USER label."""
        node = {
            "message": {
                "author": {"role": "user"},
                "content": {
                    "content_type": "text",
                    "parts": ["What is Python?"],
                },
                "metadata": {},
            }
        }
        result = format_message(node, {})
        assert "**USER:**" in result
        assert "What is Python?" in result

    def test_text_message_assistant(self):
        """Assistant text messages are formatted with ASSISTANT label."""
        node = {
            "message": {
                "author": {"role": "assistant"},
                "content": {
                    "content_type": "text",
                    "parts": ["Python is a language."],
                },
                "metadata": {},
            }
        }
        result = format_message(node, {})
        assert "**ASSISTANT:**" in result
        assert "Python is a language." in result

    def test_thinking_block_callout(self):
        """Thinking blocks are rendered as collapsed Obsidian callouts."""
        node = {
            "message": {
                "author": {"role": "assistant"},
                "content": {
                    "content_type": "thoughts",
                    "thoughts": "Let me think about this...",
                },
                "metadata": {},
            }
        }
        result = format_message(node, {})
        assert "> [!abstract]- 💭 Thinking Process" in result
        assert "> Let me think about this..." in result

    def test_thinking_block_excluded(self):
        """Thinking blocks return None when include_thinking=False."""
        node = {
            "message": {
                "author": {"role": "assistant"},
                "content": {
                    "content_type": "thoughts",
                    "thoughts": "Let me think...",
                },
                "metadata": {},
            }
        }
        result = format_message(node, {}, include_thinking=False)
        assert result is None

    def test_reasoning_recap_callout(self):
        """Reasoning recaps are rendered as collapsed info callouts."""
        node = {
            "message": {
                "author": {"role": "assistant"},
                "content": {
                    "content_type": "reasoning_recap",
                    "content": "I considered multiple approaches.",
                },
                "metadata": {},
            }
        }
        result = format_message(node, {})
        assert "> [!info]- 📋 Reasoning Summary" in result
        assert "> I considered multiple approaches." in result

    def test_code_block_format(self):
        """Code blocks are rendered as fenced code blocks with language."""
        node = {
            "message": {
                "author": {"role": "assistant"},
                "content": {
                    "content_type": "code",
                    "parts": ["print('hello')"],
                    "language": "python",
                },
                "metadata": {},
            }
        }
        result = format_message(node, {})
        assert "```python" in result
        assert "print('hello')" in result

    def test_execution_output(self):
        """Execution output is rendered as a labeled code block."""
        node = {
            "message": {
                "author": {"role": "assistant"},
                "content": {
                    "content_type": "execution_output",
                    "parts": ["Hello, World!"],
                },
                "metadata": {},
            }
        }
        result = format_message(node, {})
        assert "**Output:**" in result
        assert "Hello, World!" in result

    def test_image_link_with_attachment_map(self):
        """Image asset pointers generate proper Markdown image links."""
        node = {
            "message": {
                "author": {"role": "user"},
                "content": {
                    "content_type": "multimodal_text",
                    "parts": [
                        "Check this:",
                        {
                            "content_type": "image_asset_pointer",
                            "asset_pointer": "sediment://file_abc123",
                            "size_bytes": 50000,
                            "width": 800,
                            "height": 600,
                        },
                    ],
                },
                "metadata": {},
            }
        }
        attachment_map = {"file_abc123": "assets/image.png"}
        result = format_message(node, attachment_map)
        assert "![Image](assets/image.png)" in result

    def test_image_link_without_attachment_map(self):
        """Missing attachments show a placeholder."""
        node = {
            "message": {
                "author": {"role": "user"},
                "content": {
                    "content_type": "multimodal_text",
                    "parts": [
                        {
                            "content_type": "image_asset_pointer",
                            "asset_pointer": "sediment://file_missing",
                        },
                    ],
                },
                "metadata": {},
            }
        }
        result = format_message(node, {})
        assert "*[Image not available]*" in result

    def test_system_message_skipped(self):
        """System messages return None."""
        node = {
            "message": {
                "author": {"role": "system"},
                "content": {
                    "content_type": "text",
                    "parts": ["System prompt"],
                },
                "metadata": {},
            }
        }
        assert format_message(node, {}) is None

    def test_null_message_skipped(self):
        """Nodes with no message return None."""
        assert format_message({"message": None}, {}) is None

    def test_tether_quote_blockquote(self):
        """Tether quotes are rendered as blockquotes."""
        node = {
            "message": {
                "author": {"role": "assistant"},
                "content": {
                    "content_type": "tether_quote",
                    "parts": ["Some quoted text."],
                },
                "metadata": {},
            }
        }
        result = format_message(node, {})
        assert "> Some quoted text." in result


class TestFrontmatter:
    """Tests for frontmatter generation."""

    def test_basic_frontmatter(self, single_conversation):
        """Frontmatter includes title, date, model, and tags."""
        fm = _generate_frontmatter(single_conversation)
        assert '---' in fm
        assert 'title: "Test Conversation One"' in fm
        assert "date: 2024-03-10" in fm
        assert "model: gpt-4o" in fm
        assert "tags: [chatgpt-export, archive]" in fm

    def test_null_title_fallback(self):
        """Null title falls back to 'Untitled conversation'."""
        conv = {"title": None, "create_time": 1710072000, "mapping": {}}
        fm = _generate_frontmatter(conv)
        assert 'title: "Untitled conversation"' in fm

    def test_null_date_fallback(self):
        """Null create_time falls back to 'unknown'."""
        conv = {"title": "Test", "create_time": None, "mapping": {}}
        fm = _generate_frontmatter(conv)
        assert "date: unknown" in fm


class TestWriteSplitFiles:
    """Tests for write_split_files()."""

    def test_creates_files(self, sample_conversations, tmp_output):
        """Conversations are written to Markdown files."""
        files = write_split_files(sample_conversations, tmp_output)
        assert len(files) >= 1
        for f in files:
            assert f.exists()
            assert f.suffix == ".md"

    def test_files_have_frontmatter(self, sample_conversations, tmp_output):
        """Generated files contain YAML frontmatter."""
        files = write_split_files(sample_conversations, tmp_output)
        content = files[0].read_text(encoding="utf-8")
        assert content.startswith("---")
        assert "tags: [chatgpt-export, archive]" in content

    def test_split_respects_size_limit(self, tmp_output):
        """Large content is split across multiple files."""
        # Create many conversations with substantial content
        convs = []
        for i in range(100):
            convs.append({
                "title": f"Conversation {i}",
                "create_time": 1710072000 + i * 3600,
                "mapping": {
                    "root": {
                        "id": "root",
                        "message": None,
                        "parent": None,
                        "children": ["msg-1"],
                    },
                    "msg-1": {
                        "id": "msg-1",
                        "message": {
                            "author": {"role": "user"},
                            "content": {
                                "content_type": "text",
                                "parts": ["A" * 10000],
                            },
                            "metadata": {},
                        },
                        "parent": "root",
                        "children": [],
                    },
                },
            })

        # Split at a very small size to force multiple files
        files = write_split_files(convs, tmp_output, max_size_mb=0.01)
        assert len(files) > 1

        for f in files:
            size_mb = f.stat().st_size / (1024 * 1024)
            # Each file should be under the limit (with some tolerance
            # for the last conversation that triggered the split)
            assert size_mb < 0.1  # generous tolerance
