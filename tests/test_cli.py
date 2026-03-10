"""Tests for the CLI module."""

import json
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from byegpt.cli import app


runner = CliRunner()


class TestConvertCommand:
    """Tests for the `convert` command."""

    def test_basic_convert_from_json(self, tmp_path, sample_conversations):
        """Convert command works with a JSON file input."""
        json_file = tmp_path / "conversations.json"
        json_file.write_text(json.dumps(sample_conversations), encoding="utf-8")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "convert",
            "--input", str(json_file),
            "--output", str(output_dir),
        ])

        assert result.exit_code == 0
        assert "Migration complete" in result.stdout
        assert output_dir.exists()
        md_files = list(output_dir.glob("*.md"))
        assert len(md_files) >= 1

    def test_convert_from_zip(self, tmp_path, sample_conversations):
        """Convert command works with a ZIP file input."""
        zip_path = tmp_path / "export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("conversations.json", json.dumps(sample_conversations))

        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "convert",
            "--input", str(zip_path),
            "--output", str(output_dir),
        ])

        assert result.exit_code == 0
        assert "Migration complete" in result.stdout

    def test_convert_with_split_size(self, tmp_path, sample_conversations):
        """Convert respects custom split size."""
        json_file = tmp_path / "conversations.json"
        json_file.write_text(json.dumps(sample_conversations), encoding="utf-8")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "convert",
            "--input", str(json_file),
            "--output", str(output_dir),
            "--split-size", "10MB",
        ])

        assert result.exit_code == 0

    def test_convert_no_thinking(self, tmp_path, sample_conversations):
        """Convert with --no-thinking excludes thinking blocks."""
        json_file = tmp_path / "conversations.json"
        json_file.write_text(json.dumps(sample_conversations), encoding="utf-8")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "convert",
            "--input", str(json_file),
            "--output", str(output_dir),
            "--no-thinking",
        ])

        assert result.exit_code == 0
        assert "excluded" in result.stdout

        # Verify thinking blocks are not in the output
        for md_file in output_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            assert "Thinking Process" not in content


class TestPersonaCommand:
    """Tests for the `persona` command."""

    def test_basic_persona(self, tmp_path, sample_conversations):
        """Persona command generates a Digital Passport."""
        json_file = tmp_path / "conversations.json"
        json_file.write_text(json.dumps(sample_conversations), encoding="utf-8")
        output_file = tmp_path / "passport.md"

        result = runner.invoke(app, [
            "persona",
            "--input", str(json_file),
            "--output", str(output_file),
        ])

        assert result.exit_code == 0
        assert "Digital Passport created" in result.stdout
        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")
        assert "Digital Passport" in content
        assert "Profile Summary" in content


class TestVersionFlag:
    """Tests for the --version flag."""

    def test_version(self):
        """--version shows the version string."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "2.0.0" in result.stdout
