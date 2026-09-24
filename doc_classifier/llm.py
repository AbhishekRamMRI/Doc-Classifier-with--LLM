"""LLM classification client. No CLI dependencies."""
from __future__ import annotations

import json

from openai import OpenAI

from . import config

SYSTEM_PROMPT = """You are a document intelligence engine for a business document processing platform. You will be called once per uploaded file. You receive raw text extracted from ONE uploaded PDF and must:

1. CLASSIFY the document into EXACTLY ONE of these four fixed categories (use this exact
   lowercase snake_case label, nothing else):
   - "professional_indemnity_insurance" -- a professional indemnity insurance certificate or
     policy (also known as PI insurance or errors & omissions insurance).
   - "public_liability" -- a public liability insurance certificate or policy (also known as
     general liability insurance).
   - "invoice" -- an invoice or bill for goods/services rendered.
   - "other" -- ANYTHING that does not clearly and confidently match one of the three
     categories above (e.g. contracts, purchase orders, ID documents, other insurance types,
     resumes, bank statements, unclear/garbled content, etc.). When in doubt, use "other".

2. If -- and only if -- the document_type is "professional_indemnity_insurance" or
   "public_liability", ALSO extract these insurance-specific fields: issued_date (policy
   start date), expiry_date (policy end date), coverage_limit, coverage_currency, insurer,
   policy_number, insured_name, address (the insured party's address). Leave the
   invoice-specific fields (see below) null.

   If -- and only if -- the document_type is "invoice", ALSO extract these invoice-specific
   fields: invoice_number, invoice_date, invoice_due_date, invoice_from (issuer name/company),
   invoice_to (recipient name/company), total_amount, total_amount_currency. Leave the
   insurance-specific fields null.

   For "other", leave both insurance- and invoice-specific fields null and instead extract
   whatever general identifying fields are relevant into "extracted_fields" (freeform
   key-value pairs).

3. SCORE your confidence (0-100 integer) for the document type classification.

Return ONLY valid JSON for THIS SINGLE FILE. No markdown, no code fences, no commentary, no 
trailing commas.

OUTPUT SCHEMA:
{
  "document_type": "professional_indemnity_insurance" | "public_liability" | "invoice" | "other",
  "document_type_confidence": integer,
  "document_type_reasoning": string,
  "file_name": string,
  "file_type": "application/pdf",
  "contractor_id": string | null,
  "issued_date": string | null,
  "expiry_date": string | null,
  "coverage_limit": number | null,
  "coverage_currency": string | null,
  "insurer": string | null,
  "policy_number": string | null,
  "insured_name": string | null,
  "address": string | null,
  "invoice_number": string | null,
  "invoice_date": string | null,
  "invoice_due_date": string | null,
  "invoice_from": string | null,
  "invoice_to": string | null,
  "total_amount": number | null,
  "total_amount_currency": string | null,
  "extracted_fields": object | null,
  "extraction_confidence": integer,
  "notes": string | null
}

RULES:
- document_type MUST be one of the four exact values listed above -- never invent a new
  label or use a more specific/general variant.
- Never invent a value. If a field is not present or not confidently inferable, set it to null.
- Dates: normalize any date format found (e.g. "1st February 2025") to YYYY-MM-DD.
- Coverage limit: strip currency symbols, commas, and qualifying words ("any one claim",
  "in the aggregate") -- put ONLY the numeric primary/per-claim amount in "coverage_limit" and
  note aggregate/secondary limits in "notes".
- Confidence guidance:
  - 90-100: explicit, unambiguous label/heading found in text
  - 60-89: inferred from context, structure, or terminology but not explicitly labeled
  - Below 60: weak signal, significant ambiguity -- explain in "notes" and lean towards "other"
- If multiple documents/sections are concatenated in one PDF, classify the dominant/first one
  and note the others in "notes"."""

INVALID_JSON_FOLLOW_UP = (
    "Your last response was invalid JSON, return only valid JSON matching the schema."
)


class LLMResponseError(Exception):
    """Raised when the LLM never returns valid JSON after retrying."""


def build_user_message(document_text: str, file_name: str, contractor_id: str | None) -> str:
    return (
        f"file_name: {file_name}\n"
        f"contractor_id: {contractor_id if contractor_id else 'null'}\n\n"
        f"Extracted PDF text:\n{document_text}"
    )


def get_completion(messages: list[dict], client: OpenAI | None = None) -> str:
    """Send a chat message list to the LLM and return the raw text response."""
    client = client or OpenAI(api_key=config.require_api_key(), base_url=config.OPENAI_BASE_URL)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content or ""


def parse_json_response(raw: str) -> dict:
    """Parse raw LLM text as JSON, raising LLMResponseError on failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"LLM response was not valid JSON: {exc}") from exc
