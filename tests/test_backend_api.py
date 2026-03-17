from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from backend.app import main as main_module
from backend.app.storage import StorageManager


def _write_conversations(tmp_path: Path, sample_conversations: list[dict]) -> Path:
    path = tmp_path / "conversations.json"
    path.write_text(json.dumps(sample_conversations), encoding="utf-8")
    return path


def _build_client(tmp_path: Path) -> TestClient:
    storage_root = tmp_path / ".byegpt"
    main_module._DEMO_MODE = True
    main_module._STORAGE_DIR = storage_root
    main_module._COOKIES_PATH = storage_root / "storage.json"
    main_module._CONVERTED_DIR = storage_root / "converted"
    main_module._TUSD_UPLOAD_DIR = tmp_path / ".uploads"
    main_module._SEARCH_DIR = storage_root / "index"
    main_module._storage = StorageManager(storage_root)
    return TestClient(main_module.app)


class TestBackendApi:
    def test_convert_returns_topic_laboratory(self, tmp_path, sample_conversations):
        client = _build_client(tmp_path)
        source = _write_conversations(tmp_path, sample_conversations)

        with client:
            with source.open("rb") as handle:
                response = client.post("/convert", files={"file": ("conversations.json", handle, "application/json")})

        assert response.status_code == 200
        payload = response.json()
        assert payload["files_created"] >= 1
        assert payload["topic_laboratory"]["total_conversations"] == len(sample_conversations)
        assert payload["topic_laboratory"]["topics"]

    def test_demo_upload_and_artifact_job(self, tmp_path, sample_conversations):
        client = _build_client(tmp_path)
        source = _write_conversations(tmp_path, sample_conversations)

        with client:
            with source.open("rb") as handle:
                convert_response = client.post(
                    "/convert",
                    files={"file": ("conversations.json", handle, "application/json")},
                )
            output_dir = convert_response.json()["output_dir"]

            upload_response = client.post(
                "/notebooks/upload",
                json={"notebook_title": "Demo Notebook", "output_dir": output_dir},
            )
            assert upload_response.status_code == 200
            notebook_id = upload_response.json()["notebook_ids"][0]

            job_response = client.post(
                f"/notebooks/{notebook_id}/artifacts",
                json={"types": ["mind_map", "slides", "quiz"]},
            )
            assert job_response.status_code == 200
            job_id = job_response.json()["job_id"]

            for _ in range(20):
                status_response = client.get(f"/jobs/{job_id}")
                assert status_response.status_code == 200
                job_payload = status_response.json()
                if job_payload["status"] == "completed":
                    break
                time.sleep(0.1)
            else:  # pragma: no cover - guardrail
                raise AssertionError("Artifact job did not complete in time.")

            assert len(job_payload["artifact_ids"]) == 3
            artifact_id = job_payload["artifact_ids"][0]
            artifact_response = client.get(f"/artifacts/{artifact_id}")
            assert artifact_response.status_code == 200
            artifact_payload = artifact_response.json()
            assert artifact_payload["download_urls"]

    def test_search_index_and_query(self, tmp_path, sample_conversations):
        client = _build_client(tmp_path)
        source = _write_conversations(tmp_path, sample_conversations)

        with client:
            with source.open("rb") as handle:
                convert_response = client.post(
                    "/convert",
                    files={"file": ("conversations.json", handle, "application/json")},
                )
            output_dir = convert_response.json()["output_dir"]

            index_response = client.post("/search/index", json={"input_dir": output_dir})
            assert index_response.status_code == 200
            assert index_response.json()["document_count"] >= 1

            query_response = client.post(
                "/search/query",
                json={"text": "Python", "n_results": 3},
            )
            assert query_response.status_code == 200
            assert isinstance(query_response.json()["results"], list)
