"""FastAPI backend exposing doc_classifier over HTTP for the web UI.

Thin wrapper only: all business logic still lives in the `doc_classifier`
package and is reused as-is (same functions the CLI calls).
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from doc_classifier.processor import process_files

app = FastAPI(title="doc-classifier API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/classify")
async def classify(
    files: list[UploadFile] = File(...),
    contractor_id: str | None = Form(default=None),
) -> list[dict]:
    """Accept one or more uploaded PDF files, classify each, return results."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_paths: list[str] = []
        for upload in files:
            dest = Path(tmp_dir) / upload.filename
            with dest.open("wb") as f:
                shutil.copyfileobj(upload.file, f)
            tmp_paths.append(str(dest))

        results = process_files(tmp_paths, contractor_id=contractor_id or None)
        return [r.model_dump() for r in results]
