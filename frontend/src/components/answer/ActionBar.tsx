import { FOLLOW_ON_WORKFLOWS } from '../../lib/utils'

interface Props {
  primaryWorkflow: string
  ranWorkflows: string[]
  onRunWorkflow: (n: number) => void
  onEscalate: () => void
  escalated: boolean
  loading: boolean
}

export default function ActionBar({ primaryWorkflow, ranWorkflows, onRunWorkflow, onEscalate, escalated, loading }: Props) {
  const followOns = (FOLLOW_ON_WORKFLOWS[primaryWorkflow] ?? []).filter(
    (w) => !ranWorkflows.includes(`workflow_${w.n}`)
  )

  return (
    <div style={{
      display: 'flex', flexWrap: 'wrap', gap: '0.6rem', alignItems: 'center',
      padding: '0.85rem 1rem',
      background: 'var(--masa-white)', borderRadius: 'var(--radius-card)',
      boxShadow: 'var(--shadow-card)', borderTop: '3px solid var(--masa-harbor-tint)',
    }}>
      <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '0.82rem', color: 'var(--masa-harbor)', marginRight: '0.25rem' }}>
        What would you like to do?
      </span>

      {followOns.map((w) => (
        <button
          key={w.n}
          onClick={() => onRunWorkflow(w.n)}
          disabled={loading}
          className="btn-secondary"
          style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
        >
          {w.label}
        </button>
      ))}

      {!escalated ? (
        <button
          onClick={onEscalate}
          disabled={loading}
          style={{
            background: 'var(--masa-flare)', color: 'var(--masa-white)',
            border: 'none', borderRadius: 'var(--radius-button)',
            padding: '0.5rem 1rem', fontFamily: 'var(--font-heading)',
            fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer',
          }}
        >
          Talk to an advocate
        </button>
      ) : (
        <span style={{ fontSize: '0.85rem', color: 'var(--masa-harbor)', fontStyle: 'italic' }}>
          ✓ Escalation requested — a MASA advocate will review your case.
        </span>
      )}
    </div>
  )
}
