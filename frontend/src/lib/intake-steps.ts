import type { IntakeSubmission } from './types'

export type WidgetType =
  | 'card-picker'
  | 'currency'
  | 'text'
  | 'yes-no'
  | 'radio'
  | 'code-search'
  | 'dropdown'
  | 'network-status'

export interface StepOption {
  label: string
  value: string
  description?: string
}

export interface StepDef {
  id: string
  question: string
  field: keyof IntakeSubmission
  widget: WidgetType
  options?: StepOption[]
  optional?: boolean
  showIf?: (intake: Partial<IntakeSubmission>) => boolean
}

const BILLING_PATH = ['billing_error', 'clean_denial', 'partial_payment_underpayment']
const SURPRISE_PATH = ['surprise_out_of_network', 'balance_bill']
const COLLECTIONS_PATH = ['collections_credit_impact']
const CATAST_PATH = ['catastrophic_exposure']

const inPath = (paths: string[], intake: Partial<IntakeSubmission>) =>
  paths.includes(intake.problem_type ?? '')

export const ALL_STEPS: StepDef[] = [
  // ── Phase 1: Problem identification ──────────────────────────────────────
  {
    id: 'problem_type',
    question: "What best describes your situation?",
    field: 'problem_type',
    widget: 'card-picker',
    options: [
      { label: 'Surprise / out-of-network bill',    value: 'surprise_out_of_network',      description: 'You received a bill from a provider who was out of your insurance network' },
      { label: 'Insurance denial',                  value: 'clean_denial',                 description: 'Your insurance denied a claim or service' },
      { label: 'Partial or underpayment',           value: 'partial_payment_underpayment', description: 'Your insurance paid less than expected' },
      { label: 'Balance bill',                      value: 'balance_bill',                 description: 'A provider billed you for amounts above what your insurance paid' },
      { label: 'Billing error',                     value: 'billing_error',                description: 'You suspect there\'s a mistake on your bill or EOB' },
      { label: 'Large / catastrophic bill',         value: 'catastrophic_exposure',        description: 'You\'re facing a very large medical bill' },
      { label: 'Debt collector contact',            value: 'collections_credit_impact',    description: 'A collector is contacting you about a medical bill' },
    ],
  },
  {
    id: 'state',
    question: "Which state did you receive care in?",
    field: 'state',
    widget: 'text',
  },
  {
    id: 'insurance_situation',
    question: "What's your health insurance situation?",
    field: 'insurance_situation',
    widget: 'card-picker',
    options: [
      { label: 'Employer-sponsored insurance',  value: 'commercial_employer' },
      { label: 'Individual / marketplace plan', value: 'commercial_individual' },
      { label: 'Medicare',                      value: 'medicare_only' },
      { label: 'Medicare Advantage (Part C)',   value: 'medicare_advantage' },
      { label: 'Medicaid',                      value: 'medicaid' },
      { label: 'Uninsured / self-pay',          value: 'uninsured_self_pay' },
    ],
  },

  // ── Phase 2: Bill details — billing/denial/underpayment path ─────────────
  {
    id: 'codes_billing',
    question: "What billing codes were on your bill or EOB? (optional — skip if you don't have them)",
    field: 'codes_present',
    widget: 'code-search',
    optional: true,
    showIf: (i) => inPath(BILLING_PATH, i),
  },
  {
    id: 'amount_billed_billing',
    question: "What was the total amount billed?",
    field: 'amount_billed',
    widget: 'currency',
    optional: true,
    showIf: (i) => inPath(BILLING_PATH, i),
  },
  {
    id: 'amount_plan_paid',
    question: "How much did your insurance pay?",
    field: 'amount_plan_paid',
    widget: 'currency',
    optional: true,
    showIf: (i) => inPath(BILLING_PATH, i),
  },
  {
    id: 'amount_patient_responsibility_billing',
    question: "What is your current balance owed?",
    field: 'amount_patient_responsibility',
    widget: 'currency',
    optional: true,
    showIf: (i) => inPath(BILLING_PATH, i),
  },
  {
    id: 'denial_present',
    question: "Was there a denial notice on your Explanation of Benefits (EOB)?",
    field: 'denial_present',
    widget: 'yes-no',
    showIf: (i) => inPath(BILLING_PATH, i),
  },
  {
    id: 'denial_reason_text',
    question: "What reason did they give for the denial?",
    field: 'denial_reason_text',
    widget: 'text',
    optional: true,
    showIf: (i) => inPath(BILLING_PATH, i) && i.denial_present === true,
  },

  // ── Phase 2: Bill details — surprise/balance bill path ───────────────────
  {
    id: 'ambulance_involved',
    question: "Was an ambulance involved?",
    field: 'ambulance_involved',
    widget: 'yes-no',
    showIf: (i) => inPath(SURPRISE_PATH, i),
  },
  {
    id: 'ambulance_type',
    question: "Was it air or ground transport?",
    field: 'ambulance_type',
    widget: 'radio',
    options: [
      { label: 'Ground ambulance', value: 'ground' },
      { label: 'Air ambulance',    value: 'air' },
      { label: "I'm not sure",     value: 'unknown' },
    ],
    showIf: (i) => inPath(SURPRISE_PATH, i) && i.ambulance_involved === true,
  },
  {
    id: 'codes_ambulance',
    question: "What was the HCPCS code on the bill? (optional — look for codes starting with A04)",
    field: 'codes_present',
    widget: 'code-search',
    optional: true,
    showIf: (i) => inPath(SURPRISE_PATH, i) && i.ambulance_involved === true,
  },
  {
    id: 'facility_network_status',
    question: "Was the facility (hospital / clinic) in your insurance network?",
    field: 'facility_network_status',
    widget: 'network-status',
    showIf: (i) => inPath(SURPRISE_PATH, i),
  },
  {
    id: 'provider_network_status',
    question: "Was the provider (doctor / ambulance company) in your network?",
    field: 'provider_network_status',
    widget: 'network-status',
    showIf: (i) => inPath(SURPRISE_PATH, i),
  },
  {
    id: 'amount_billed_surprise',
    question: "What was the total amount billed?",
    field: 'amount_billed',
    widget: 'currency',
    optional: true,
    showIf: (i) => inPath(SURPRISE_PATH, i),
  },
  {
    id: 'amount_patient_responsibility_surprise',
    question: "What is your current balance owed?",
    field: 'amount_patient_responsibility',
    widget: 'currency',
    optional: true,
    showIf: (i) => inPath(SURPRISE_PATH, i),
  },
  {
    id: 'notice_consent_claimed',
    question: "Did the provider claim you signed a notice-and-consent waiver?",
    field: 'notice_consent_claimed',
    widget: 'yes-no',
    showIf: (i) => inPath(SURPRISE_PATH, i),
  },
  {
    id: 'gfe_received',
    question: "Did you receive a Good Faith Estimate before the service?",
    field: 'gfe_received',
    widget: 'yes-no',
    showIf: (i) => inPath(SURPRISE_PATH, i) && i.insurance_situation === 'uninsured_self_pay',
  },

  // ── Phase 2: Collections path ─────────────────────────────────────────────
  {
    id: 'in_collections',
    question: "Has this debt been sent to a collection agency?",
    field: 'in_collections',
    widget: 'yes-no',
    showIf: (i) => inPath(COLLECTIONS_PATH, i),
  },
  {
    id: 'reported_to_credit',
    question: "Has it been reported to your credit bureau?",
    field: 'reported_to_credit',
    widget: 'yes-no',
    showIf: (i) => inPath(COLLECTIONS_PATH, i),
  },
  {
    id: 'debt_validated',
    question: "Have you received written debt validation from the collector?",
    field: 'debt_validated',
    widget: 'yes-no',
    showIf: (i) => inPath(COLLECTIONS_PATH, i),
  },

  // ── Phase 2: Catastrophic path ────────────────────────────────────────────
  {
    id: 'amount_billed_catastrophic',
    question: "What is the total amount you're facing?",
    field: 'amount_billed',
    widget: 'currency',
    optional: true,
    showIf: (i) => inPath(CATAST_PATH, i),
  },
  {
    id: 'amount_patient_responsibility_catastrophic',
    question: "What is your current balance owed?",
    field: 'amount_patient_responsibility',
    widget: 'currency',
    optional: true,
    showIf: (i) => inPath(CATAST_PATH, i),
  },

  // ── Phase 3: MASA membership ──────────────────────────────────────────────
  {
    id: 'is_masa_member',
    question: "Are you a MASA member?",
    field: 'is_masa_member',
    widget: 'yes-no',
  },
  {
    id: 'masa_plan_tier',
    question: "What is your MASA plan tier?",
    field: 'masa_plan_tier',
    widget: 'dropdown',
    optional: true,
    options: [
      { label: 'Emergency Shield Plus', value: 'Emergency Shield Plus' },
      { label: 'Lifetime',              value: 'Lifetime' },
      { label: 'Other / not sure',      value: 'Other' },
    ],
    showIf: (i) => i.is_masa_member === true,
  },

  // ── Phase 4: Advocacy capacity ────────────────────────────────────────────
  {
    id: 'advocacy_capacity',
    question: "How much support would you like from SAM?",
    field: 'advocacy_capacity',
    widget: 'card-picker',
    options: [
      { label: 'Guide me step by step', value: 'needs_hand_holding', description: 'Walk me through each option with explanations' },
      { label: 'Give me the full picture', value: 'self_directed',   description: 'I can handle next steps once I understand the situation' },
      { label: 'Handle this for me',    value: 'needs_proxy',        description: 'I need someone to manage this on my behalf' },
    ],
  },
]

export function getActiveSteps(intake: Partial<IntakeSubmission>): StepDef[] {
  return ALL_STEPS.filter((s) => !s.showIf || s.showIf(intake))
}
