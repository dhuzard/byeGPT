from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from backend.app import main as main_module
from backend.app.cloud import NotebookUploadError
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
    def test_persona_returns_taxonomy(self, tmp_path, sample_conversations):
        client = _build_client(tmp_path)
        source = _write_conversations(tmp_path, sample_conversations)

        with client:
            with source.open("rb") as handle:
                response = client.post(
                    "/persona",
                    files={"file": ("conversations.json", handle, "application/json")},
                )

        assert response.status_code == 200
        payload = response.json()
        assert payload["passport_id"]
        assert payload["taxonomy"]["categories"]
        taxonomy_response = client.get(f"/passports/{payload['passport_id']}/taxonomy")
        assert taxonomy_response.status_code == 200
        assert taxonomy_response.json()["version"] == "2.0"

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
        assert payload["taxonomy"]["categories"]

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
            notebook_response = client.get(f"/notebooks/{notebook_id}")
            assert notebook_response.status_code == 200
            assert notebook_response.json()["kind"] == "master"

    def test_demo_extended_artifact_job(self, tmp_path, sample_conversations):
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
                json={"notebook_title": "Extended Demo Notebook", "output_dir": output_dir},
            )
            notebook_id = upload_response.json()["notebook_ids"][0]

            job_response = client.post(
                f"/notebooks/{notebook_id}/artifacts",
                json={"types": ["video", "cinematic_video", "flashcards", "infographic", "data_table"]},
            )
            assert job_response.status_code == 200
            job_id = job_response.json()["job_id"]

            for _ in range(20):
                status_response = client.get(f"/jobs/{job_id}")
                job_payload = status_response.json()
                if job_payload["status"] == "completed":
                    break
                time.sleep(0.1)
            else:  # pragma: no cover - guardrail
                raise AssertionError("Extended artifact job did not complete in time.")

            assert len(job_payload["artifact_ids"]) == 5
            artifact_payloads = [
                client.get(f"/artifacts/{artifact_id}").json()
                for artifact_id in job_payload["artifact_ids"]
            ]
            artifact_types = {artifact["type"] for artifact in artifact_payloads}
            assert artifact_types == {"video", "cinematic_video", "flashcards", "infographic", "data_table"}

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

    def test_create_derived_notebook(self, tmp_path, sample_conversations):
        client = _build_client(tmp_path)
        source = _write_conversations(tmp_path, sample_conversations)

        with client:
            with source.open("rb") as handle:
                convert_response = client.post(
                    "/convert",
                    files={"file": ("conversations.json", handle, "application/json")},
                )
            output_dir = convert_response.json()["output_dir"]

            with source.open("rb") as handle:
                passport_response = client.post(
                    "/persona",
                    files={"file": ("conversations.json", handle, "application/json")},
                )
            passport_payload = passport_response.json()
            taxonomy = passport_payload["taxonomy"]
            first_category = taxonomy["categories"][0]
            first_subcategory = first_category["subcategories"][0]

            derived_response = client.post(
                "/notebooks/derived",
                json={
                    "title": "Focused Notebook",
                    "passport_id": passport_payload["passport_id"],
                    "parent_output_dir": output_dir,
                    "selections": [
                        {
                            "category": first_category["slug"],
                            "subcategory": first_subcategory["slug"],
                        }
                    ],
                },
            )

            assert derived_response.status_code == 200
            notebook = derived_response.json()
            assert notebook["kind"] == "thematic"
            assert notebook["selection_filters"]

            sources_response = client.get(f"/notebooks/{notebook['notebook_id']}/sources")
            assert sources_response.status_code == 200
            assert sources_response.json()["source_count"] >= 1

    def test_demo_notebook_chat(self, tmp_path, sample_conversations):
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
            notebook_id = upload_response.json()["notebook_ids"][0]

            chat_response = client.post(
                f"/notebooks/{notebook_id}/chat",
                json={"question": "What is this notebook about?"},
            )
            assert chat_response.status_code == 200
            payload = chat_response.json()
            assert payload["answer"]
            assert payload["conversation_id"]

            history_response = client.get(f"/notebooks/{notebook_id}/chat")
            assert history_response.status_code == 200
            assert "turns" in history_response.json()

    def test_upload_returns_gateway_timeout_when_notebooklm_times_out(self, tmp_path, monkeypatch):
        client = _build_client(tmp_path)
        main_module._DEMO_MODE = False
        output_dir = tmp_path / "converted"
        output_dir.mkdir()
        (output_dir / "sample.md").write_text("# Sample\n", encoding="utf-8")

        async def _failing_batch_upload(*args, **kwargs):
            raise NotebookUploadError(
                "NotebookLM timed out while adding source 'sample'. Try the upload again.",
                status_code=504,
            )

        monkeypatch.setattr(main_module, "batch_upload", _failing_batch_upload)
        monkeypatch.setattr(main_module, "is_authenticated", lambda path: True)

        with client:
            upload_response = client.post(
                "/notebooks/upload",
                json={"notebook_title": "Timeout Notebook", "output_dir": str(output_dir)},
            )

        assert upload_response.status_code == 504
        assert "timed out while adding source" in upload_response.json()["detail"]
