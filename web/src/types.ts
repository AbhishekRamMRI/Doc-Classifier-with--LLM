export interface DocumentResult {
  document_type: string
  document_type_confidence: number
  document_type_reasoning: string
  file_name: string
  file_type: string
  contractor_id: string | null
  issued_date: string | null
  expiry_date: string | null
  coverage_limit: number | null
  coverage_currency: string | null
  insurer: string | null
  policy_number: string | null
  insured_name: string | null
  extracted_fields: Record<string, unknown> | null
  extraction_confidence: number
  notes: string | null
}
