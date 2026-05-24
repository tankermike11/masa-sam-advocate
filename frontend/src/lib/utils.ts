export function fmtCurrency(n: number | null | undefined): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

export function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export const PROBLEM_LABELS: Record<string, string> = {
  surprise_out_of_network:      'Surprise / out-of-network bill',
  clean_denial:                 'Insurance denial',
  partial_payment_underpayment: 'Underpayment or partial coverage',
  balance_bill:                 'Balance bill',
  billing_error:                'Billing error',
  billing_explanation:          'Understand my bill / EOB',
  catastrophic_exposure:        'Large / catastrophic bill',
  collections_credit_impact:    'Collections or credit issue',
}

export const INSURANCE_LABELS: Record<string, string> = {
  commercial_employer:   'Employer-sponsored insurance',
  commercial_individual: 'Individual / marketplace plan',
  medicare_only:         'Medicare',
  medicare_advantage:    'Medicare Advantage (Part C)',
  medicaid:              'Medicaid',
  uninsured_self_pay:    'Uninsured / self-pay',
}

export const WORKFLOW_LABELS: Record<string, string> = {
  workflow_1: 'Bill Explanation',
  workflow_2: 'Surprise Bill / Ambulance',
  workflow_3: 'Document Generation',
  workflow_4: 'Collections Guidance',
  workflow_5: 'General Guidance',
}

// Which additional workflows to offer after primary, per primary workflow
export const FOLLOW_ON_WORKFLOWS: Record<string, { label: string; n: number }[]> = {
  workflow_1: [
    { label: 'Get advocacy documents', n: 3 },
    { label: 'Explore my options',     n: 5 },
  ],
  workflow_2: [
    { label: 'Get advocacy documents', n: 3 },
    { label: 'Explore my options',     n: 5 },
  ],
  workflow_3: [{ label: 'Explore my options', n: 5 }],
  workflow_4: [{ label: 'Explore my options', n: 5 }],
  workflow_5: [],
}
