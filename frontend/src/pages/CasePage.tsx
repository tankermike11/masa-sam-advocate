import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { getActiveSteps } from '../lib/intake-steps'
import type { StepDef } from '../lib/intake-steps'
import type { AnswerCard as AnswerCardType, CaseResponse, EscalationResponse, IntakeSubmission, TriageResult } from '../lib/types'
import { PROBLEM_LABELS, INSURANCE_LABELS } from '../lib/utils'
import CardPicker from '../components/intake/CardPicker'
import YesNoToggle from '../components/intake/YesNoToggle'
import RadioGroup from '../components/intake/RadioGroup'
import CodeSearchWidget from '../components/intake/CodeSearchWidget'
import NetworkStatusPicker from '../components/intake/NetworkStatusPicker'
import AnswerCardComponent from '../components/answer/AnswerCard'
import ActionBar from '../components/answer/ActionBar'
import DocumentViewer from '../components/answer/DocumentViewer'
import EscalationModal from '../components/answer/EscalationModal'
import LoadingSpinner from '../components/shared/LoadingSpinner'

type Phase = 'intake' | 'review' | 'loading' | 'result'

function buildIntakePayload(raw: Record<string, unknown>): IntakeSubmission {
  return {
    insurance_situation: raw.insurance_situation as string,
    state: (raw.state as string || '').toUpperCase(),
    problem_type: raw.problem_type as string,
    denial_present: (raw.denial_present as boolean) ?? false,
    denial_reason_text: raw.denial_reason_text as string | null ?? null,
    ambulance_involved: (raw.ambulance_involved as boolean) ?? false,
    ambulance_type: raw.ambulance_type as string | null ?? null,
    codes_present: (raw.codes_present as IntakeSubmission['codes_present']) ?? [],
    amount_billed: raw.amount_billed as number | null ?? null,
    amount_plan_paid: raw.amount_plan_paid as number | null ?? null,
    amount_patient_responsibility: raw.amount_patient_responsibility as number | null ?? null,
    facility_network_status: (raw.facility_network_status as string) || 'unknown',
    provider_network_status: (raw.provider_network_status as string) || 'unknown',
    notice_consent_claimed: (raw.notice_consent_claimed as boolean) ?? false,
    gfe_received: (raw.gfe_received as boolean) ?? false,
    gfe_expected_charges: (raw.gfe_expected_charges as IntakeSubmission['gfe_expected_charges']) ?? [],
    in_collections: (raw.in_collections as boolean) ?? false,
    reported_to_credit: (raw.reported_to_credit as boolean) ?? false,
    debt_validated: (raw.debt_validated as boolean) ?? false,
    is_masa_member: (raw.is_masa_member as boolean) ?? false,
    masa_plan_tier: raw.masa_plan_tier as string | null ?? null,
    advocacy_capacity: (raw.advocacy_capacity as string) || 'needs_hand_holding',
  }
}

export default function CasePage() {
  const location = useLocation()
  const nav = useNavigate()
  const scrollRef = useRef<HTMLDivElement>(null)
  const prefill = (location.state as { prefill?: IntakeSubmission } | null)?.prefill

  const [phase, setPhase] = useState<Phase>(prefill ? 'review' : 'intake')
  const [intake, setIntake] = useState<Record<string, unknown>>(prefill ? { ...prefill } : {})
  const [activeStepIdx, setActiveStepIdx] = useState(0)
  const [completedAnswers, setCompletedAnswers] = useState<{ question: string; answer: string }[]>([])

  // Result state
  const [caseId, setCaseId] = useState<string | null>(() => sessionStorage.getItem('sam_case_id'))
  const [triageResult, setTriageResult] = useState<TriageResult | null>(null)
  const [workflowResults, setWorkflowResults] = useState<Record<string, AnswerCardType>>({})
  const [documents, setDocuments] = useState<Record<string, unknown>>({})
  const [runningWorkflow, setRunningWorkflow] = useState<string | null>(null)
  const [escalated, setEscalated] = useState(false)
  const [escalationResult, setEscalationResult] = useState<EscalationResponse | null>(null)
  const [showEscalationModal, setShowEscalationModal] = useState(false)
  const [escalationLoading, setEscalationLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCaseDrawer, setShowCaseDrawer] = useState(false)

  // Restore session
  useEffect(() => {
    const saved = sessionStorage.getItem('sam_case_id')
    if (saved && !prefill) {
      setCaseId(saved)
      api.getCase(saved)
        .then((detail) => {
          setTriageResult(detail.triage_result as unknown as TriageResult)
          setWorkflowResults(detail.workflow_outputs as Record<string, AnswerCardType>)
          setDocuments(detail.generated_documents)
          setPhase('result')
        })
        .catch(() => { /* stale session — proceed normally */ })
    }
  }, [])

  const scrollToBottom = () => {
    setTimeout(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' }), 80)
  }

  const activeSteps = getActiveSteps(intake as Record<string, unknown>)
  const currentStep: StepDef | undefined = activeSteps[activeStepIdx]

  // Advance on answer
  const handleAnswer = (field: string, value: unknown) => {
    const updated = { ...intake, [field]: value }
    setIntake(updated)

    const step = activeSteps[activeStepIdx]
    const displayVal = formatAnswer(field, value)
    setCompletedAnswers((prev) => [...prev, { question: step.question, answer: displayVal }])

    const recomputed = getActiveSteps(updated as Record<string, unknown>)
    const nextIdx = activeStepIdx + 1
    if (nextIdx < recomputed.length) {
      setActiveStepIdx(nextIdx)
      scrollToBottom()
    } else {
      setPhase('review')
      scrollToBottom()
    }
  }

  const handleSkip = () => {
    const step = activeSteps[activeStepIdx]
    setCompletedAnswers((prev) => [...prev, { question: step.question, answer: '(skipped)' }])
    const recomputed = getActiveSteps(intake as Record<string, unknown>)
    const nextIdx = activeStepIdx + 1
    if (nextIdx < recomputed.length) {
      setActiveStepIdx(nextIdx)
    } else {
      setPhase('review')
    }
    scrollToBottom()
  }

  const submitCase = async () => {
    setPhase('loading')
    try {
      const payload = buildIntakePayload(intake)
      const caseResp: CaseResponse = await api.createCase(payload)
      setCaseId(caseResp.case_id)
      setTriageResult(caseResp.triage_result)
      sessionStorage.setItem('sam_case_id', caseResp.case_id)

      // Auto-run primary workflow
      const n = parseInt(caseResp.triage_result.primary_workflow.replace('workflow_', ''), 10)
      const wfResp = await api.runWorkflow(caseResp.case_id, n)
      setWorkflowResults({ [wfResp.workflow]: wfResp.answer_card })

      setPhase('result')
      scrollToBottom()
    } catch (e) {
      setError((e as Error).message)
      setPhase('review')
    }
  }

  const runWorkflow = async (n: number) => {
    if (!caseId) return
    const key = `workflow_${n}`
    setRunningWorkflow(key)
    try {
      const resp = await api.runWorkflow(caseId, n)
      setWorkflowResults((prev) => ({ ...prev, [resp.workflow]: resp.answer_card }))
      if (n === 3) {
        // Fetch documents after workflow 3
        const detail = await api.getCase(caseId)
        setDocuments(detail.generated_documents)
      }
      scrollToBottom()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setRunningWorkflow(null)
    }
  }

  const doEscalate = async () => {
    if (!caseId) return
    setEscalationLoading(true)
    try {
      const resp = await api.escalate(caseId)
      setEscalationResult(resp)
      setEscalated(true)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setEscalationLoading(false)
    }
  }

  const startNew = () => {
    sessionStorage.removeItem('sam_case_id')
    setPhase('intake')
    setIntake({})
    setActiveStepIdx(0)
    setCompletedAnswers([])
    setCaseId(null)
    setTriageResult(null)
    setWorkflowResults({})
    setDocuments({})
    setEscalated(false)
    setEscalationResult(null)
    setError(null)
    nav('/case', { replace: true })
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ background: 'var(--masa-horizon)', padding: '0.85rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 50 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 28, height: 28, background: 'var(--masa-tide)', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'white', fontSize: '0.95rem' }}>+</div>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--masa-white)', fontSize: '0.95rem' }}>SAM</span>
          {phase === 'result' && triageResult && (
            <span className="chip" style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.15)', color: 'white' }}>
              {PROBLEM_LABELS[triageResult.problem_type] ?? triageResult.problem_type}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {phase === 'result' && (
            <>
              <button onClick={() => setShowCaseDrawer((s) => !s)} style={{ background: 'none', border: '1px solid rgba(255,255,255,0.3)', borderRadius: 'var(--radius-button)', color: 'var(--masa-white)', padding: '0.3rem 0.6rem', fontSize: '0.78rem', cursor: 'pointer', fontFamily: 'var(--font-body)' }}>
                {'{ }'}
              </button>
              <button onClick={startNew} style={{ background: 'none', border: '1px solid rgba(255,255,255,0.3)', borderRadius: 'var(--radius-button)', color: 'var(--masa-white)', padding: '0.3rem 0.7rem', fontSize: '0.78rem', cursor: 'pointer', fontFamily: 'var(--font-body)' }}>
                New case
              </button>
            </>
          )}
          <a href="/" style={{ color: 'var(--masa-white)', opacity: 0.6, fontSize: '0.78rem', textDecoration: 'none' }}>← Home</a>
        </div>
      </div>

      {/* Chat thread */}
      <div
        ref={scrollRef}
        style={{ flex: 1, overflowY: 'auto', padding: 'var(--chat-padding)', display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: 'var(--max-width)', margin: '0 auto', width: '100%' }}
      >
        {/* Completed intake history */}
        {completedAnswers.map((qa, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <SamBubble>{qa.question}</SamBubble>
            <MemberBubble>{qa.answer}</MemberBubble>
          </div>
        ))}

        {/* Current intake step */}
        {phase === 'intake' && currentStep && (
          <div>
            <SamBubble>{currentStep.question}</SamBubble>
            <div style={{ marginTop: '0.6rem' }}>
              <StepWidget step={currentStep} intake={intake} onAnswer={handleAnswer} onSkip={handleSkip} />
            </div>
          </div>
        )}

        {/* Review screen */}
        {phase === 'review' && (
          <div>
            <SamBubble>Here's what you told me. Does everything look right?</SamBubble>
            <div style={{ background: 'var(--masa-white)', borderRadius: 'var(--radius-card)', boxShadow: 'var(--shadow-card)', padding: '1rem', marginTop: '0.75rem' }}>
              <ReviewSummary intake={intake} />
              {error && <p style={{ color: 'var(--masa-flare)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>Error: {error}</p>}
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button onClick={() => { setPhase('intake'); setActiveStepIdx(0); setCompletedAnswers([]) }} className="btn-secondary" style={{ fontSize: '0.88rem' }}>
                  Edit answers
                </button>
                <button onClick={submitCase} className="btn-horizon" style={{ fontSize: '0.88rem' }}>
                  Analyze my case →
                </button>
              </div>
              <details style={{ marginTop: '0.75rem' }}>
                <summary style={{ fontSize: '0.78rem', color: 'var(--masa-harbor)', cursor: 'pointer' }}>View case data (JSON)</summary>
                <pre style={{ fontSize: '0.72rem', background: 'var(--masa-harbor-tint)', padding: '0.5rem', borderRadius: 4, marginTop: '0.25rem', overflow: 'auto', maxHeight: 200, fontFamily: 'monospace' }}>
                  {JSON.stringify(buildIntakePayload(intake), null, 2)}
                </pre>
              </details>
            </div>
          </div>
        )}

        {/* Loading */}
        {phase === 'loading' && (
          <div>
            <SamBubble>Got it — let me review your case.</SamBubble>
            <LoadingSpinner />
          </div>
        )}

        {/* Results */}
        {phase === 'result' && triageResult && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <SamBubble>
              I've reviewed your case. Here's my assessment.
            </SamBubble>

            {/* Workflow answer cards */}
            {Object.entries(workflowResults).map(([key, card]) => (
              <AnswerCardComponent key={key} card={card} />
            ))}

            {/* Generated documents */}
            {Object.keys(documents).length > 0 && (
              <DocumentViewer documents={documents as Parameters<typeof DocumentViewer>[0]['documents']} />
            )}

            {/* Running another workflow */}
            {runningWorkflow && <LoadingSpinner message={`Running ${runningWorkflow}…`} />}

            {/* Action bar */}
            {!runningWorkflow && (
              <ActionBar
                primaryWorkflow={triageResult.primary_workflow}
                ranWorkflows={Object.keys(workflowResults)}
                onRunWorkflow={runWorkflow}
                onEscalate={() => setShowEscalationModal(true)}
                escalated={escalated}
                loading={!!runningWorkflow}
              />
            )}
          </div>
        )}
      </div>

      {/* Case data drawer */}
      {showCaseDrawer && caseId && (
        <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: 'var(--masa-white)', borderTop: '2px solid var(--masa-horizon)', padding: '1rem', zIndex: 100, maxHeight: '40vh', overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--masa-horizon)', fontSize: '0.88rem' }}>Case Data (Eval Harness JSON)</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={() => navigator.clipboard.writeText(JSON.stringify(buildIntakePayload(intake), null, 2))} className="btn-secondary" style={{ fontSize: '0.78rem', padding: '0.3rem 0.7rem' }}>Copy intake JSON</button>
              <button onClick={() => setShowCaseDrawer(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.1rem', color: 'var(--masa-harbor)' }}>×</button>
            </div>
          </div>
          <pre style={{ fontSize: '0.72rem', fontFamily: 'monospace', background: 'var(--masa-harbor-tint)', padding: '0.5rem', borderRadius: 4, overflow: 'auto', margin: 0 }}>
            {JSON.stringify(buildIntakePayload(intake), null, 2)}
          </pre>
        </div>
      )}

      {/* Escalation modal */}
      {showEscalationModal && (
        <EscalationModal
          onConfirm={doEscalate}
          onCancel={() => setShowEscalationModal(false)}
          result={escalationResult}
          loading={escalationLoading}
        />
      )}
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SamBubble({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-start' }}>
      <div style={{ width: 28, height: 28, background: 'var(--masa-tide)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: '0.8rem', color: 'white', fontFamily: 'var(--font-heading)', fontWeight: 700, marginTop: 2 }}>S</div>
      <div style={{ background: 'var(--masa-horizon)', color: 'var(--masa-white)', borderRadius: '0 var(--radius-bubble) var(--radius-bubble) var(--radius-bubble)', padding: '0.7rem 0.9rem', fontSize: '0.92rem', lineHeight: 1.5, maxWidth: '85%' }}>
        {children}
      </div>
    </div>
  )
}

function MemberBubble({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
      <div style={{ background: 'var(--masa-harbor-tint)', color: 'var(--masa-body)', borderRadius: 'var(--radius-bubble) 0 var(--radius-bubble) var(--radius-bubble)', padding: '0.6rem 0.9rem', fontSize: '0.9rem', maxWidth: '75%' }}>
        {children}
      </div>
    </div>
  )
}

// Holds its own local state so typing doesn't advance the step on every keystroke.
// Only calls onAnswer when the user explicitly clicks Continue or presses Enter.
function CurrencyStepWidget({ field, onAnswer, onSkip }: {
  field: string
  onAnswer: (f: string, v: unknown) => void
  onSkip?: () => void
}) {
  const [localValue, setLocalValue] = useState<number | null>(null)
  const [skipped, setSkipped] = useState(false)

  const handleContinue = () => {
    if (localValue !== null) onAnswer(field, localValue)
  }

  const handleSkip = () => {
    setSkipped(true)
    if (onSkip) onSkip()
  }

  if (skipped) return null

  return (
    <div style={{ marginTop: '0.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--masa-horizon)', fontSize: '1.1rem' }}>$</span>
        <input
          type="number"
          min={0}
          step="0.01"
          placeholder="0.00"
          value={localValue ?? ''}
          onChange={(e) => setLocalValue(e.target.value ? Number(e.target.value) : null)}
          onKeyDown={(e) => { if (e.key === 'Enter' && localValue !== null) handleContinue() }}
          style={{
            border: '2px solid var(--masa-harbor-tint)', borderRadius: 'var(--radius-button)',
            padding: '0.6rem 0.8rem', fontSize: '1rem', width: '200px',
            outline: 'none', transition: 'border-color 0.15s',
          }}
          onFocus={(e) => (e.target.style.borderColor = 'var(--masa-tide)')}
          onBlur={(e) => (e.target.style.borderColor = 'var(--masa-harbor-tint)')}
          autoFocus
        />
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.6rem', alignItems: 'center' }}>
        <button
          onClick={handleContinue}
          disabled={localValue === null}
          className="btn-primary"
          style={{ fontSize: '0.88rem', padding: '0.5rem 1rem' }}
        >
          Continue
        </button>
        {onSkip && (
          <button
            onClick={handleSkip}
            style={{ background: 'none', border: 'none', color: 'var(--masa-harbor)', fontSize: '0.8rem', cursor: 'pointer', fontFamily: 'var(--font-body)', textDecoration: 'underline' }}
          >
            Skip / I don't know
          </button>
        )}
      </div>
    </div>
  )
}

function StepWidget({ step, intake, onAnswer, onSkip }: {
  step: StepDef
  intake: Record<string, unknown>
  onAnswer: (field: string, value: unknown) => void
  onSkip: () => void
}) {
  const field = step.field as string
  const val = intake[field]

  switch (step.widget) {
    case 'card-picker':
      return (
        <CardPicker
          options={step.options ?? []}
          value={val as string ?? null}
          onChange={(v) => onAnswer(field, v)}
        />
      )
    case 'yes-no':
      return (
        <div>
          <YesNoToggle value={val as boolean ?? null} onChange={(v) => onAnswer(field, v)} />
          {step.optional && <button onClick={onSkip} style={{ marginTop: '0.5rem', background: 'none', border: 'none', color: 'var(--masa-harbor)', fontSize: '0.8rem', cursor: 'pointer', fontFamily: 'var(--font-body)', textDecoration: 'underline' }}>Skip</button>}
        </div>
      )
    case 'radio':
      return (
        <RadioGroup
          options={step.options ?? []}
          value={val as string ?? null}
          onChange={(v) => onAnswer(field, v)}
        />
      )
    case 'network-status':
      return (
        <NetworkStatusPicker value={val as string ?? null} onChange={(v) => onAnswer(field, v)} />
      )
    case 'currency':
      return (
        <CurrencyStepWidget
          field={field}
          onAnswer={onAnswer}
          onSkip={step.optional ? onSkip : undefined}
        />
      )
    case 'text':
      return (
        <TextStepWidget field={field} value={val as string ?? ''} onAnswer={onAnswer} onSkip={step.optional ? onSkip : undefined} placeholder={field === 'state' ? 'e.g. FL, TX, CA…' : 'Type your answer…'} />
      )
    case 'dropdown':
      return (
        <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <select
            value={val as string ?? ''}
            onChange={(e) => { if (e.target.value) onAnswer(field, e.target.value) }}
            style={{ border: '2px solid var(--masa-harbor-tint)', borderRadius: 'var(--radius-button)', padding: '0.6rem 0.8rem', fontSize: '1rem', maxWidth: 280 }}
          >
            <option value="">Select…</option>
            {(step.options ?? []).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          {step.optional && (
            <button onClick={onSkip} style={{ background: 'none', border: 'none', color: 'var(--masa-harbor)', fontSize: '0.8rem', cursor: 'pointer', fontFamily: 'var(--font-body)', textDecoration: 'underline', textAlign: 'left' }}>Skip</button>
          )}
        </div>
      )
    case 'code-search':
      return (
        <div>
          <CodeSearchWidget value={(val as IntakeSubmission['codes_present']) ?? []} onChange={(codes) => { intake[field] = codes }} />
          <button onClick={() => onAnswer(field, val ?? [])} className="btn-primary" style={{ marginTop: '0.6rem', fontSize: '0.88rem', padding: '0.5rem 1rem' }}>
            {(val as unknown[])?.length ? `Continue with ${(val as unknown[]).length} code(s)` : 'Skip / No codes'}
          </button>
        </div>
      )
    default:
      return null
  }
}

function TextStepWidget({ field, value, onAnswer, onSkip, placeholder }: {
  field: string; value: string; onAnswer: (f: string, v: unknown) => void
  onSkip?: () => void; placeholder?: string
}) {
  const [local, setLocal] = useState(value)
  return (
    <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'flex-start', flexDirection: 'column' }}>
      <input
        type="text"
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        placeholder={placeholder}
        onKeyDown={(e) => { if (e.key === 'Enter' && local.trim()) onAnswer(field, local.trim()) }}
        style={{ border: '2px solid var(--masa-harbor-tint)', borderRadius: 'var(--radius-button)', padding: '0.6rem 0.8rem', fontSize: '1rem', width: '100%', maxWidth: 300 }}
        onFocus={(e) => (e.target.style.borderColor = 'var(--masa-tide)')}
        onBlur={(e) => (e.target.style.borderColor = 'var(--masa-harbor-tint)')}
        autoFocus
      />
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button onClick={() => { if (local.trim()) onAnswer(field, local.trim()) }} disabled={!local.trim()} className="btn-primary" style={{ fontSize: '0.88rem', padding: '0.5rem 1rem' }}>
          Continue
        </button>
        {onSkip && <button onClick={onSkip} style={{ background: 'none', border: 'none', color: 'var(--masa-harbor)', fontSize: '0.8rem', cursor: 'pointer', fontFamily: 'var(--font-body)', textDecoration: 'underline' }}>Skip</button>}
      </div>
    </div>
  )
}

function ReviewSummary({ intake }: { intake: Record<string, unknown> }) {
  const items: [string, string][] = [
    ['Problem', PROBLEM_LABELS[intake.problem_type as string] ?? intake.problem_type as string],
    ['State', intake.state as string],
    ['Insurance', INSURANCE_LABELS[intake.insurance_situation as string] ?? intake.insurance_situation as string],
  ]
  if (intake.amount_billed) items.push(['Billed', `$${Number(intake.amount_billed).toLocaleString()}`])
  if (intake.amount_patient_responsibility) items.push(['Balance owed', `$${Number(intake.amount_patient_responsibility).toLocaleString()}`])
  if (intake.ambulance_involved) items.push(['Ambulance', intake.ambulance_type as string ?? 'yes'])
  if (intake.denial_present) items.push(['Denial', 'Yes'])
  if (intake.is_masa_member) items.push(['MASA member', `Yes — ${intake.masa_plan_tier ?? 'plan tier not specified'}`])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '0.65rem' }}>
      {items.map(([label, val]) => (
        <div key={label}>
          <div style={{ fontSize: '0.73rem', color: 'var(--masa-harbor)', fontFamily: 'var(--font-heading)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.15rem' }}>{label}</div>
          <div style={{ fontSize: '0.9rem', color: 'var(--masa-body)' }}>{val}</div>
        </div>
      ))}
    </div>
  )
}

function formatAnswer(field: string, value: unknown): string {
  if (value === true) return 'Yes'
  if (value === false) return 'No'
  if (Array.isArray(value)) {
    if (value.length === 0) return '(none)'
    return value.map((v) => typeof v === 'object' && v !== null && 'code' in v ? `${(v as { code_type: string; code: string }).code_type} ${(v as { code_type: string; code: string }).code}` : String(v)).join(', ')
  }
  if (field === 'insurance_situation') return INSURANCE_LABELS[value as string] ?? String(value)
  if (field === 'problem_type') return PROBLEM_LABELS[value as string] ?? String(value)
  if (field === 'advocacy_capacity') {
    const map: Record<string, string> = { needs_hand_holding: 'Guide me step by step', self_directed: 'Give me the full picture', needs_proxy: 'Handle this for me' }
    return map[value as string] ?? String(value)
  }
  if (typeof value === 'number') return `$${value.toLocaleString()}`
  return String(value)
}
