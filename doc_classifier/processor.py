"""Per-file orchestration: PDF extraction -> LLM classification -> validation.

Pure business logic, no CLI/web dependencies. Reusable by any front-end.
"""
from __future__ import annotations

from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from . import llm
from .pdf_extract import PDFExtractionError, extract_text_from_pdf
from .schema import DOCUMENT_TYPES, DocumentResult


def _normalize_document_type(data: dict) -> None:
    """Force document_type to one of the fixed DOCUMENT_TYPES, falling back to "other".

    Defense-in-depth: even if the LLM ignores the prompt's fixed label list, the
    UI/CLI must never see an unrecognized document_type.
    """
    raw_type = str(data.get("document_type", "")).strip().lower()
    if raw_type not in DOCUMENT_TYPES:
        if raw_type and raw_type != "other":
            note = f"Model returned unrecognized document type '{raw_type}'; shown as 'other'."
            existing_notes = data.get("notes")
            data["notes"] = f"{existing_notes} {note}" if existing_notes else note
        data["document_type"] = "other"
    else:
        data["document_type"] = raw_type


def _error_result(file_name: str, message: str, contractor_id: str | None = None) -> DocumentResult:
    return DocumentResult(
        document_type="error",
        document_type_confidence=0,
        document_type_reasoning="",
        file_name=file_name,
        contractor_id=contractor_id,
        extraction_confidence=0,
        notes=message,
    )


def process_file(
    file_path: str | Path,
    contractor_id: str | None = None,
    client: OpenAI | None = None,
) -> DocumentResult:
    """Run the full classification pipeline for a single PDF file.

    Never raises: any failure (extraction, API, invalid/unvalidatable LLM output)
    is captured and returned as an error DocumentResult instead.
    """
    file_name = Path(file_path).name

    try:
        document_text = extract_text_from_pdf(file_path)
    except PDFExtractionError as exc:
        return _error_result(file_name, str(exc), contractor_id)

    messages = [
        {"role": "system", "content": llm.SYSTEM_PROMPT},
        {
            "role": "user",
            "content": llm.build_user_message(document_text, file_name, contractor_id),
        },
    ]

    last_error: Exception | None = None
    raw = ""
    for _ in range(2):
        try:
            raw = llm.get_completion(messages, client=client)
            data = llm.parse_json_response(raw)
            data.setdefault("file_name", file_name)
            data.setdefault("contractor_id", contractor_id)
            _normalize_document_type(data)
            return DocumentResult(**data)
        except (llm.LLMResponseError, ValidationError) as exc:
            last_error = exc
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": llm.INVALID_JSON_FOLLOW_UP})
        except Exception as exc:  # noqa: BLE001 - API/network errors shouldn't crash the batch
            return _error_result(file_name, f"LLM request failed: {exc}", contractor_id)

    return _error_result(
        file_name,
        f"LLM response was invalid after retry: {last_error}",
        contractor_id,
    )


def process_files(
    file_paths: list[str | Path],
    contractor_id: str | None = None,
    client: OpenAI | None = None,
) -> list[DocumentResult]:
    """Run process_file for each path, collecting results in order. Never raises."""
    return [process_file(path, contractor_id=contractor_id, client=client) for path in file_paths]
