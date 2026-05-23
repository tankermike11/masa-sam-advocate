import type { EscalationResponse } from '../../lib/types'

interface Props {
  onConfirm: () => void
  onCancel: () => void
  result: EscalationResponse | null
  loading: boolean
}

export default function EscalationModal({ onConfirm, onCancel, result, loading }: Props) {
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(35,8,113,0.55)', zIndex: 200,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem',
    }}>
      <div style={{
        background: 'var(--masa-white)', borderRadius: 'var(--radius-card)',
        boxShadow: 'var(--shadow-modal)', padding: '2rem', maxWidth: 480, width: '100%',
      }}>
        {!result ? (
          <>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Request a human advocate</h2>
            <p style={{ color: 'var(--masa-body)', fontSize: '0.93rem', marginBottom: '1.5rem' }}>
              A MASA advocate will personally review your full case, including all the analysis SAM has prepared.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button onClick={onCancel} className="btn-secondary" style={{ fontSize: '0.9rem' }}>Cancel</button>
              <button onClick={onConfirm} disabled={loading} className="btn-horizon" style={{ fontSize: '0.9rem' }}>
                {loading ? 'Submitting…' : 'Request advocate'}
              </button>
            </div>
          </>
        ) : (
          <>
            <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>✓</div>
              <h2 style={{ fontSize: '1.2rem', marginBottom: '0.25rem' }}>Case submitted</h2>
            </div>

            <div style={{
              background: result.gate_decision.fee_applies ? '#fff3e0' : '#e8f5e9',
              border: `1px solid ${result.gate_decision.fee_applies ? '#ffb74d' : '#a5d6a7'}`,
              borderRadius: 'var(--radius-card)', padding: '0.85rem', marginBottom: '1rem', fontSize: '0.9rem',
            }}>
              {result.message}
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--masa-harbor)', marginBottom: '1rem' }}>
              Case ID: <code style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{result.case_id}</code>
            </p>

            <button onClick={onCancel} className="btn-primary" style={{ width: '100%', fontSize: '0.95rem' }}>
              Close
            </button>
          </>
        )}
      </div>
    </div>
  )
}
