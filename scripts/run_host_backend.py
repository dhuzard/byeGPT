from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)

    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "backend"))
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root / "core"))

    os.environ.setdefault("BYEGPT_STORAGE", str(repo_root / ".byegpt"))
    os.environ.setdefault("BYEGPT_DEMO_MODE", "false")
    os.environ.setdefault(
        "CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:3000,http://localhost:3000",
    )

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        app_dir=str(repo_root / "backend"),
    )


if __name__ == "__main__":
    main()
