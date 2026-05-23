import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import type { AnswerCard as AnswerCardType, CaseDetail } from '../lib/types'
import { fmtCurrency, fmtDate, PROBLEM_LABELS, INSURANCE_LABELS, WORKFLOW_LABELS } from '../lib/utils'
import AnswerCard from '../components/answer/AnswerCard'
import DocumentViewer from '../components/answer/DocumentViewer'
import SeverityBadge from '../components/shared/SeverityBadge'

export default function AdminCaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const nav = useNavigate()
  const [detail, setDetail] = useState<CaseDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [openPanels, setOpenPanels] = useState<Set<string>>(new Set(['header', 'triage']))

  useEffect(() => {
    if (!caseId) return
    api.getCase(caseId)
      .then(setDetail)
      .catch((e) => setError(e.message))
  }, [caseId])

  const toggle = (p: string) => setOpenPanels((prev) => {
    const s = new Set(prev)
    s.has(p) ? s.delete(p) : s.add(p)
    return s
  })

  const tr = detail?.triage_result as Record<string, unknown> | undefined

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ background: 'var(--masa-horizon)', padding: '1rem 2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button onClick={() => nav('/admin')} style={{ background: 'none', border: 'none', color: 'var(--masa-white)', opacity: 0.7, fontSize: '0.85rem', cursor: 'pointer', fontFamily: 'var(--font-body)' }}>← Queue</button>
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--masa-white)', fontSize: '1rem' }}>
          Case Detail
        </span>
        {detail && <span style={{ fontFamily: 'monospace', color: 'var(--masa-white)', opacity: 0.6, fontSize: '0.8rem' }}>{detail.case_id}</span>}
      </div>

      <div style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: '1.5rem 1.25rem', width: '100%', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {error && <p style={{ color: 'var(--masa-flare)' }}>Error: {error}</p>}
        {!detail && !error && <p style={{ color: 'var(--masa-harbor)' }}>Loading…</p>}

        {detail && (
          <>
            {/* Header panel */}
            <Panel id="header" label="Case Overview" open={openPanels.has('header')} onToggle={toggle}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '0.75rem' }}>
                {[
                  ['Status', <span className={`badge badge-${detail.escalation_status}`}>{detail.escalation_status}</span>],
                  ['Submitted', fmtDate(detail.created_at)],
                  ['Problem', PROBLEM_LABELS[tr?.problem_type as string] ?? tr?.problem_type],
                  ['Insurance', INSURANCE_LABELS[tr?.insurance_situation as string] ?? tr?.insurance_situation],
                  ['Severity', <SeverityBadge severity={tr?.severity as string ?? 'unknown'} />],
                  ['Dollar at stake', fmtCurrency((detail.intake as Record<string, unknown>).amount_patient_responsibility as number)],
                ].map(([label, val], i) => (
                  <div key={i}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--masa-harbor)', fontFamily: 'var(--font-heading)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.2rem' }}>{label as string}</div>
                    <div style={{ fontSize: '0.9rem' }}>{val as React.ReactNode}</div>
                  </div>
                ))}
              </div>
              {detail.gate_decision && (
                <div style={{ marginTop: '0.75rem', padding: '0.65rem 0.9rem', background: (detail.gate_decision as { fee_applies?: boolean }).fee_applies ? '#fff3e0' : '#e8f5e9', borderRadius: 'var(--radius-card)', fontSize: '0.85rem' }}>
                  <strong>Gate decision:</strong> {(detail.gate_decision as { message?: string }).message}
                </div>
              )}
            </Panel>

            {/* Triage panel */}
            <Panel id="triage" label="Triage Result" open={openPanels.has('triage')} onToggle={toggle}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <span className="chip">Primary: {WORKFLOW_LABELS[tr?.primary_workflow as string] ?? tr?.primary_workflow as string}</span>
                {(tr?.rule_modules as string[] ?? []).map((m: string) => <span key={m} className="chip">{m}</span>)}
              </div>
              {(tr?.escalation_reasons as string[] ?? []).length > 0 && (
                <div style={{ fontSize: '0.85rem', color: 'var(--masa-body)' }}>
                  Escalation reasons: {(tr?.escalation_reasons as string[]).join(', ')}
                </div>
              )}
            </Panel>

            {/* Workflow outputs */}
            {Object.entries(detail.workflow_outputs).map(([wfKey, card]) => (
              <Panel key={wfKey} id={wfKey} label={`${WORKFLOW_LABELS[wfKey] ?? wfKey} — Answer Card`} open={openPanels.has(wfKey)} onToggle={toggle}>
                <AnswerCard card={card as AnswerCardType} />
              </Panel>
            ))}

            {/* Generated documents */}
            {Object.keys(detail.generated_documents).length > 0 && (
              <Panel id="docs" label="Generated Documents" open={openPanels.has('docs')} onToggle={toggle}>
                <DocumentViewer documents={detail.generated_documents} />
              </Panel>
            )}

            {/* Raw JSON */}
            <Panel id="raw" label="Raw Case JSON" open={openPanels.has('raw')} onToggle={toggle}>
              <pre style={{ fontSize: '0.75rem', background: 'var(--masa-harbor-tint)', padding: '0.75rem', borderRadius: 'var(--radius-card)', overflow: 'auto', maxHeight: 300, margin: 0, fontFamily: 'monospace' }}>
                {JSON.stringify(detail, null, 2)}
              </pre>
            </Panel>
          </>
        )}
      </div>
    </div>
  )
}

function Panel({ id, label, open, onToggle, children }: {
  id: string; label: string; open: boolean; onToggle: (id: string) => void; children: React.ReactNode
}) {
  return (
    <div style={{ background: 'var(--masa-white)', borderRadius: 'var(--radius-card)', boxShadow: 'var(--shadow-card)', overflow: 'hidden' }}>
      <button
        onClick={() => onToggle(id)}
        style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.85rem 1.1rem', background: 'none', border: 'none', cursor: 'pointer', borderBottom: open ? '1px solid var(--masa-harbor-tint)' : 'none' }}
      >
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '0.9rem', color: 'var(--masa-horizon)' }}>{label}</span>
        <span style={{ color: 'var(--masa-harbor)' }}>{open ? '▼' : '▶'}</span>
      </button>
      {open && <div style={{ padding: '1rem 1.1rem' }}>{children}</div>}
    </div>
  )
}
