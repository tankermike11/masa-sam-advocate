import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import type { CaseSummary } from '../lib/types'
import { fmtCurrency, fmtDate, PROBLEM_LABELS } from '../lib/utils'
import SeverityBadge from '../components/shared/SeverityBadge'

export default function AdminQueuePage() {
  const nav = useNavigate()
  const [cases, setCases] = useState<CaseSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    api.getQueue()
      .then((r) => { setCases(r.cases); setTotal(r.total) })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const statusBadge = (s: string) => (
    <span className={`badge badge-${s}`} style={{ textTransform: 'capitalize' }}>{s.replace('_', ' ')}</span>
  )

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ background: 'var(--masa-horizon)', padding: '1rem 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 30, height: 30, background: 'var(--masa-tide)', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'white', fontSize: '1rem' }}>+</div>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--masa-white)', fontSize: '1rem' }}>MASA Advocate Queue</span>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span style={{ color: 'var(--masa-white)', opacity: 0.7, fontSize: '0.85rem' }}>{total} case{total !== 1 ? 's' : ''} escalated</span>
          <button onClick={load} style={{ background: 'var(--masa-tide)', color: 'white', border: 'none', borderRadius: 'var(--radius-button)', padding: '0.4rem 0.85rem', fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer' }}>↻ Refresh</button>
          <a href="/" style={{ color: 'var(--masa-white)', opacity: 0.7, fontSize: '0.82rem', textDecoration: 'none' }}>← Member view</a>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '1.5rem 1.25rem', width: '100%' }}>
        {loading && <p style={{ color: 'var(--masa-harbor)' }}>Loading queue…</p>}
        {error && <p style={{ color: 'var(--masa-flare)' }}>Error: {error}</p>}

        {!loading && !error && cases.length === 0 && (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--masa-harbor)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📭</div>
            <p>No escalated cases yet. Cases appear here when members request an advocate or the engine recommends one.</p>
          </div>
        )}

        {cases.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {cases.map((c) => (
              <div
                key={c.case_id}
                onClick={() => nav(`/admin/cases/${c.case_id}`)}
                style={{
                  background: 'var(--masa-white)', borderRadius: 'var(--radius-card)',
                  boxShadow: 'var(--shadow-card)', padding: '1rem 1.25rem', cursor: 'pointer',
                  borderLeft: '4px solid var(--masa-tide)', transition: 'box-shadow 0.15s',
                  display: 'grid', gridTemplateColumns: '1fr auto', gap: '0.75rem', alignItems: 'center',
                }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.boxShadow = '0 4px 16px rgba(35,8,113,0.15)')}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.boxShadow = 'var(--shadow-card)')}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                    {statusBadge(c.escalation_status)}
                    <SeverityBadge severity={c.severity} size="sm" />
                    <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '0.9rem', color: 'var(--masa-horizon)' }}>
                      {PROBLEM_LABELS[c.problem_type] ?? c.problem_type}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--masa-harbor)' }}>
                      {fmtDate(c.created_at)}
                    </span>
                    {c.dollar_at_stake != null && (
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--masa-flare)' }}>
                        {fmtCurrency(c.dollar_at_stake)} at stake
                      </span>
                    )}
                    {c.workflow_outputs_present.length > 0 && (
                      <span style={{ fontSize: '0.78rem', color: 'var(--masa-harbor)' }}>
                        Workflows run: {c.workflow_outputs_present.join(', ')}
                      </span>
                    )}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  {c.gate_decision && (
                    <span style={{
                      fontSize: '0.78rem', fontFamily: 'var(--font-heading)', fontWeight: 600,
                      color: (c.gate_decision as { fee_applies?: boolean }).fee_applies ? 'var(--masa-flare)' : '#2e7d32',
                    }}>
                      {(c.gate_decision as { fee_applies?: boolean }).fee_applies ? 'Fee applies' : 'Covered'}
                    </span>
                  )}
                  <div style={{ fontSize: '0.75rem', color: 'var(--masa-harbor)', marginTop: '0.2rem' }}>
                    {c.case_id.slice(0, 8)}…
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
