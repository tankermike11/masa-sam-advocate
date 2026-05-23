import type { IntakeSubmission } from './types'

export interface Scenario {
  id: string
  title: string
  description: string
  tags: string[]
  lookFor: string[]
  intake: IntakeSubmission
  expectedWorkflow: string
}

export const SCENARIOS: Scenario[] = [
  {
    id: 'ground-ambulance-masa',
    title: 'Ground Ambulance — MASA Member',
    description: 'Emergency ground transport billed $2,400. MASA Emergency Shield Plus member. Plan paid $450. Patient owes $1,950.',
    tags: ['Ground Ambulance', 'MASA Member', '$1,950 at stake', 'Emergency Shield Plus'],
    lookFor: [
      'Federal gap explanation (NSA does NOT protect ground ambulance)',
      'Medicare reference rate for A0427 in FL as negotiation anchor',
      'MASA gap-coverage routing',
      'Escalation fee waived (Emergency Shield Plus)',
    ],
    expectedWorkflow: 'workflow_2',
    intake: {
      insurance_situation: 'commercial_employer',
      state: 'FL',
      problem_type: 'surprise_out_of_network',
      service_type: 'emergency',
      facility_network_status: 'in_network',
      provider_network_status: 'out_of_network',
      ambulance_involved: true,
      ambulance_type: 'ground',
      codes_present: [{ code_type: 'HCPCS', code: 'A0427' }],
      amount_billed: 2400.00,
      amount_plan_paid: 450.00,
      amount_patient_responsibility: 1950.00,
      is_masa_member: true,
      masa_plan_tier: 'Emergency Shield Plus',
      advocacy_capacity: 'needs_hand_holding',
    },
  },
  {
    id: 'surprise-oon-denial',
    title: 'Surprise OON Bill — Insurance Denial',
    description: 'OON emergency physician at in-network hospital. Claim denied. $3,200 billed. NSA protections may apply.',
    tags: ['Surprise Bill', 'OON Provider', 'Denial', '$3,200'],
    lookFor: [
      'NSA rule engine evaluation (categories A, B, C, D, E)',
      'Emergency services protection — OON provider at in-network facility',
      'Escalation recommendation (all NSA rules are draft)',
      'Internal appeal document option via Workflow 3',
    ],
    expectedWorkflow: 'workflow_2',
    intake: {
      insurance_situation: 'commercial_employer',
      state: 'TX',
      problem_type: 'surprise_out_of_network',
      service_type: 'emergency',
      facility_network_status: 'in_network',
      provider_network_status: 'out_of_network',
      ambulance_involved: false,
      amount_billed: 3200.00,
      amount_patient_responsibility: 3200.00,
      denial_present: true,
      denial_reason_text: 'Out-of-network provider',
      is_masa_member: false,
      advocacy_capacity: 'needs_hand_holding',
    },
  },
  {
    id: 'billing-error-medicare',
    title: 'Billing Error — Medicare Advantage Member',
    description: 'Medicare Advantage member. ICD-10 and HCPCS codes on EOB they cannot interpret. $850 patient responsibility.',
    tags: ['Billing Error', 'Medicare Advantage', 'Code Decode', '$850'],
    lookFor: [
      'ICD-10 code I10 (Essential hypertension) decoded',
      'HCPCS code A0425 (ground ambulance mileage) decoded',
      'Bill-level dollar reconciliation',
      'Workflow 3 option for itemized bill request',
    ],
    expectedWorkflow: 'workflow_1',
    intake: {
      insurance_situation: 'medicare_advantage',
      state: 'FL',
      problem_type: 'billing_error',
      codes_present: [
        { code_type: 'ICD10CM', code: 'I10' },
        { code_type: 'HCPCS',   code: 'A0425' },
      ],
      amount_billed: 1200.00,
      amount_plan_paid: 350.00,
      amount_patient_responsibility: 850.00,
      denial_present: false,
      is_masa_member: false,
      advocacy_capacity: 'self_directed',
    },
  },
  {
    id: 'collections-fdcpa',
    title: 'Collections — Credit Harassment',
    description: 'Medical bill sent to collections and reported to credit bureaus. Member doesn\'t know their FDCPA rights.',
    tags: ['Collections', 'Credit Bureau', 'FDCPA', 'Debt Validation'],
    lookFor: [
      'FDCPA rights explained plainly',
      'Debt validation letter template pre-filled with FL details',
      'CFPB complaint routing',
      'Credit report dispute guidance',
    ],
    expectedWorkflow: 'workflow_4',
    intake: {
      insurance_situation: 'commercial_employer',
      state: 'CA',
      problem_type: 'collections_credit_impact',
      in_collections: true,
      reported_to_credit: true,
      debt_validated: false,
      amount_patient_responsibility: 2800.00,
      is_masa_member: false,
      advocacy_capacity: 'needs_hand_holding',
    },
  },
  {
    id: 'self-pay-ppdr',
    title: 'Self-Pay PPDR Pathway',
    description: 'Uninsured patient. Received Good Faith Estimate for $900. Billed $1,800. Qualifies for Patient-Provider Dispute Resolution.',
    tags: ['Uninsured', 'Self-Pay', 'GFE', 'PPDR', '$900 discrepancy'],
    lookFor: [
      'GFE vs. actual charge discrepancy ($900 above estimate)',
      'PPDR eligibility explained (≥$400 threshold)',
      'PPDR initiation document generated',
      '120-day deadline surfaced',
    ],
    expectedWorkflow: 'workflow_2',
    intake: {
      insurance_situation: 'uninsured_self_pay',
      state: 'FL',
      problem_type: 'surprise_out_of_network',
      ambulance_involved: false,
      facility_network_status: 'unknown',
      provider_network_status: 'out_of_network',
      amount_billed: 1800.00,
      amount_patient_responsibility: 1800.00,
      gfe_received: true,
      gfe_expected_charges: [{ provider_name: 'ABC Medical Center', expected_charge: 900.00 }],
      is_masa_member: false,
      advocacy_capacity: 'needs_hand_holding',
    },
  },
]
