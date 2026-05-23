export interface CodeEntry {
  code_type: string
  code: string
}

export interface GfeProvider {
  provider_name: string | null
  expected_charge: number | null
}

export interface IntakeSubmission {
  insurance_situation: string
  state: string
  problem_type: string
  plan_funding_type?: string
  plan_identifier?: string | null
  codes_present?: CodeEntry[]
  amount_billed?: number | null
  amount_allowed?: number | null
  amount_plan_paid?: number | null
  amount_patient_responsibility?: number | null
  denial_present?: boolean
  denial_codes?: string[]
  denial_reason_text?: string | null
  service_type?: string | null
  facility_network_status?: string
  provider_network_status?: string
  ambulance_involved?: boolean
  ambulance_type?: string | null
  notice_consent_claimed?: boolean
  notice_timestamp?: string | null
  service_timestamp?: string | null
  appointment_lead_time?: number | null
  gfe_received?: boolean
  gfe_expected_charges?: GfeProvider[]
  in_collections?: boolean
  reported_to_credit?: boolean
  debt_validated?: boolean
  is_masa_member?: boolean
  masa_plan_tier?: string | null
  advocacy_capacity?: string
}

export interface TriageResult {
  problem_type: string
  insurance_situation: string
  severity: string
  advocacy_capacity: string
  primary_workflow: string
  rule_modules: string[]
  escalation_recommendation: string
  escalation_reasons: string[]
}

export interface Citation {
  source_id: string
  publisher: string | null
  canonical_url: string | null
}

export interface AnswerCard {
  workflow: string
  what_we_found: string[]
  what_it_likely_means: string[]
  citations: Citation[]
  confidence: Record<string, string>
  what_needs_verification: string[]
  recommended_next_step: string
  dollar_at_stake: number | null
  escalation_recommendation: string
  disclaimer: string
}

export interface CaseResponse {
  case_id: string
  created_at: string
  triage_result: TriageResult
}

export interface WorkflowResponse {
  case_id: string
  workflow: string
  answer_card: AnswerCard
}

export interface GateDecision {
  fee_applies: boolean
  message: string
  tier_matched: string | null
}

export interface EscalationResponse {
  case_id: string
  escalation_status: string
  gate_decision: GateDecision
  message: string
}

export interface CaseSummary {
  case_id: string
  created_at: string
  escalation_status: string
  severity: string
  problem_type: string
  insurance_situation: string
  advocacy_capacity: string
  dollar_at_stake: number | null
  escalation_reasons: string[]
  gate_decision: Record<string, unknown> | null
  workflow_outputs_present: string[]
}

export interface QueueResponse {
  cases: CaseSummary[]
  total: number
}

export interface CaseDetail {
  case_id: string
  created_at: string
  escalation_status: string
  gate_decision: Record<string, unknown> | null
  intake: Record<string, unknown>
  triage_result: Record<string, unknown>
  workflow_outputs: Record<string, AnswerCard>
  generated_documents: Record<string, GeneratedDocument>
}

export interface GeneratedDocument {
  document_type: string
  content: string
  citations: Citation[]
  disclaimer: string
  counsel_required: boolean
}

export interface CodeSearchResult {
  code: string
  code_type: string
  description: string | null
  short_description: string | null
  source_id: string
  fallback?: string
}
