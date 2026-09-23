"""Pydantic schema for the LLM's structured document classification output."""
from __future__ import annotations

from pydantic import BaseModel, Field

# Fixed set of document types the classifier is restricted to. Anything that
# doesn't clearly match one of the specific categories is normalized to "other"
# (see doc_classifier.processor.normalize_document_type).
DOCUMENT_TYPES: tuple[str, ...] = (
    "professional_indemnity_insurance",
    "public_liability",
    "invoice",
    "other",
)


class DocumentResult(BaseModel):
    document_type: str
    document_type_confidence: int = Field(ge=0, le=100)
    document_type_reasoning: str
    file_name: str
    file_type: str = "application/pdf"
    contractor_id: str | None = None
    issued_date: str | None = None
    expiry_date: str | None = None
    coverage_limit: float | None = None
    coverage_currency: str | None = None
    insurer: str | None = None
    policy_number: str | None = None
    insured_name: str | None = None
    extracted_fields: dict | None = None
    extraction_confidence: int = Field(ge=0, le=100)
    notes: str | None = None

