from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class StorageManager:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.passports_dir = self.root / "passports"
        self.artifacts_dir = self.root / "artifacts"
        self.notebooks_dir = self.root / "notebooks"

    @property
    def passports_index(self) -> Path:
        return self.passports_dir / "index.json"

    @property
    def artifacts_index(self) -> Path:
        return self.artifacts_dir / "index.json"

    @property
    def notebooks_index(self) -> Path:
        return self.notebooks_dir / "index.json"

    def save_passport(self, markdown: str) -> dict[str, Any]:
        return self.save_passport_bundle(markdown=markdown, taxonomy=None)

    def save_passport_bundle(
        self,
        *,
        markdown: str,
        taxonomy: dict[str, Any] | None,
    ) -> dict[str, Any]:
        passport_id = f"passport_{uuid.uuid4().hex[:12]}"
        created_at = utcnow_iso()
        path = self.passports_dir / f"{passport_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        taxonomy_path = self.passports_dir / f"{passport_id}.taxonomy.json"
        if taxonomy is not None:
            _write_json(taxonomy_path, taxonomy)

        metadata = {
            "passport_id": passport_id,
            "created_at": created_at,
            "path": str(path),
            "taxonomy_path": str(taxonomy_path) if taxonomy is not None else None,
            "taxonomy_version": taxonomy.get("version") if taxonomy else None,
        }
        index = _read_json(self.passports_index, {})
        index[passport_id] = metadata
        _write_json(self.passports_index, index)
        return metadata

    def get_passport(self, passport_id: str) -> dict[str, Any] | None:
        index = _read_json(self.passports_index, {})
        metadata = index.get(passport_id)
        if not metadata:
            return None
        return metadata

    def get_passport_taxonomy(self, passport_id: str) -> dict[str, Any] | None:
        metadata = self.get_passport(passport_id)
        if not metadata:
            return None
        taxonomy_path = metadata.get("taxonomy_path")
        if not taxonomy_path:
            return None
        path = Path(taxonomy_path)
        if not path.exists():
            return None
        return _read_json(path, None)

    def register_notebook(
        self,
        *,
        notebook_id: str,
        title: str,
        output_dir: Path,
        source_paths: list[Path],
        kind: str = "master",
        passport_id: str | None = None,
        taxonomy_version: str | None = None,
        parent_notebook_id: str | None = None,
        selection_filters: list[dict[str, str]] | None = None,
        source_count: int | None = None,
        conversation_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        index = _read_json(self.notebooks_index, {})
        record = {
            "notebook_id": notebook_id,
            "title": title,
            "kind": kind,
            "output_dir": str(Path(output_dir)),
            "source_paths": [str(Path(path)) for path in source_paths],
            "source_count": source_count if source_count is not None else len(source_paths),
            "created_at": utcnow_iso(),
            "passport_id": passport_id,
            "taxonomy_version": taxonomy_version,
            "parent_notebook_id": parent_notebook_id,
            "selection_filters": selection_filters or [],
            "conversation_ids": conversation_ids or [],
        }
        index[notebook_id] = record
        _write_json(self.notebooks_index, index)
        return record

    def attach_passport_to_notebooks(
        self,
        notebook_ids: list[str],
        passport_id: str | None,
    ) -> None:
        if not passport_id:
            return
        index = _read_json(self.notebooks_index, {})
        changed = False
        for notebook_id in notebook_ids:
            record = index.get(notebook_id)
            if not record:
                continue
            record["passport_id"] = passport_id
            changed = True
        if changed:
            _write_json(self.notebooks_index, index)

    def get_notebook(self, notebook_id: str) -> dict[str, Any] | None:
        index = _read_json(self.notebooks_index, {})
        return index.get(notebook_id)

    def list_notebooks(self) -> list[dict[str, Any]]:
        index = _read_json(self.notebooks_index, {})
        notebooks = list(index.values())
        notebooks.sort(key=lambda item: item.get("created_at", ""))
        return notebooks

    def list_notebook_artifacts(self, notebook_id: str) -> list[dict[str, Any]]:
        index = _read_json(self.artifacts_index, {})
        artifacts = [meta for meta in index.values() if meta.get("notebook_id") == notebook_id]
        artifacts.sort(key=lambda item: item.get("created_at", ""))
        return artifacts

    def create_artifact(
        self,
        *,
        notebook_id: str,
        artifact_type: str,
        upstream_artifact_id: str | None = None,
    ) -> dict[str, Any]:
        artifact_id = f"artifact_{uuid.uuid4().hex[:12]}"
        artifact_dir = self.artifacts_dir / notebook_id / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        metadata = {
            "artifact_id": artifact_id,
            "notebook_id": notebook_id,
            "type": artifact_type,
            "status": "ready",
            "upstream_artifact_id": upstream_artifact_id,
            "created_at": utcnow_iso(),
            "updated_at": utcnow_iso(),
            "files": {},
            "preview": None,
        }
        self._write_artifact_metadata(metadata)
        return metadata

    def add_artifact_file(
        self,
        artifact_id: str,
        fmt: str,
        *,
        content: bytes | str,
        filename: str,
        preview: Any | None = None,
    ) -> dict[str, Any]:
        metadata = self.get_artifact(artifact_id)
        if metadata is None:
            raise FileNotFoundError(f"Artifact '{artifact_id}' not found.")

        artifact_dir = self.artifacts_dir / metadata["notebook_id"] / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        file_path = artifact_dir / filename
        if isinstance(content, str):
            file_path.write_text(content, encoding="utf-8")
        else:
            file_path.write_bytes(content)

        metadata["files"][fmt] = str(file_path)
        if preview is not None:
            metadata["preview"] = preview
        metadata["updated_at"] = utcnow_iso()
        self._write_artifact_metadata(metadata)
        return metadata

    def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        index = _read_json(self.artifacts_index, {})
        metadata_path = index.get(artifact_id)
        if not metadata_path:
            return None
        return _read_json(Path(metadata_path), {})

    def get_artifact_file(self, artifact_id: str, fmt: str) -> Path | None:
        metadata = self.get_artifact(artifact_id)
        if metadata is None:
            return None
        file_path = metadata.get("files", {}).get(fmt)
        if not file_path:
            return None
        path = Path(file_path)
        return path if path.exists() else None

    def create_notebook_export(self, notebook_id: str) -> Path:
        notebook = self.get_notebook(notebook_id)
        if notebook is None:
            raise FileNotFoundError(f"Notebook '{notebook_id}' not found.")

        export_dir = self.root / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        archive_path = export_dir / f"{notebook_id}.zip"

        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as zf:
            output_dir = Path(notebook["output_dir"])
            if output_dir.exists():
                for path in output_dir.rglob("*"):
                    if path.is_file():
                        zf.write(path, arcname=f"markdown/{path.relative_to(output_dir)}")

            passport_id = notebook.get("passport_id")
            if passport_id:
                passport = self.get_passport(passport_id)
                if passport:
                    passport_path = Path(passport["path"])
                    if passport_path.exists():
                        zf.write(passport_path, arcname=f"passport/{passport_path.name}")
                    taxonomy_path = passport.get("taxonomy_path")
                    if taxonomy_path and Path(taxonomy_path).exists():
                        zf.write(taxonomy_path, arcname=f"passport/{Path(taxonomy_path).name}")

            notebook_json = self.root / "exports" / f"{notebook_id}.notebook.json"
            _write_json(notebook_json, notebook)
            zf.write(notebook_json, arcname="notebook/metadata.json")
            notebook_json.unlink(missing_ok=True)

            for artifact in self.list_notebook_artifacts(notebook_id):
                for file_path in artifact.get("files", {}).values():
                    path = Path(file_path)
                    if path.exists():
                        zf.write(
                            path,
                            arcname=f"artifacts/{artifact['artifact_id']}/{path.name}",
                        )

        return archive_path

    def _write_artifact_metadata(self, metadata: dict[str, Any]) -> None:
        metadata_path = (
            self.artifacts_dir
            / metadata["notebook_id"]
            / metadata["artifact_id"]
            / "metadata.json"
        )
        _write_json(metadata_path, metadata)
        index = _read_json(self.artifacts_index, {})
        index[metadata["artifact_id"]] = str(metadata_path)
        _write_json(self.artifacts_index, index)


def build_markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "| Column | Value |\n|---|---|\n| status | empty |\n"

    headers = list(rows[0].keys())
    lines = [
        f"| {' | '.join(headers)} |",
        f"| {' | '.join('---' for _ in headers)} |",
    ]
    for row in rows:
        lines.append(f"| {' | '.join(str(row.get(header, '')) for header in headers)} |")
    return "\n".join(lines) + "\n"


def build_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "status,value\nempty,true\n"

    headers = list(rows[0].keys())
    escaped_headers = ",".join(headers)
    lines = [escaped_headers]
    for row in rows:
        values: list[str] = []
        for header in headers:
            value = str(row.get(header, ""))
            if any(char in value for char in [",", "\"", "\n"]):
                value = '"' + value.replace('"', '""') + '"'
            values.append(value)
        lines.append(",".join(values))
    return "\n".join(lines) + "\n"


def derive_slide_table_rows(slides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, slide in enumerate(slides, start=1):
        rows.append(
            {
                "slide": index,
                "title": slide.get("title", f"Slide {index}"),
                "content": slide.get("content", ""),
            }
        )
    return rows
