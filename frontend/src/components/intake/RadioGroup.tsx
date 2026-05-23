import type { StepOption } from '../../lib/intake-steps'

interface Props {
  options: StepOption[]
  value: string | null
  onChange: (v: string) => void
}

export default function RadioGroup({ options, value, onChange }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
      {options.map((opt) => {
        const selected = value === opt.value
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.75rem',
              background: selected ? 'var(--masa-horizon)' : 'var(--masa-white)',
              color: selected ? 'var(--masa-white)' : 'var(--masa-body)',
              border: `2px solid ${selected ? 'var(--masa-horizon)' : 'var(--masa-harbor-tint)'}`,
              borderRadius: 'var(--radius-card)',
              padding: '0.7rem 1rem', textAlign: 'left', cursor: 'pointer',
              fontFamily: 'var(--font-body)', fontSize: '0.95rem', transition: 'all 0.15s',
            }}
          >
            <span style={{
              width: 16, height: 16, borderRadius: '50%', flexShrink: 0,
              background: selected ? 'var(--masa-white)' : 'var(--masa-harbor-tint)',
              border: `2px solid ${selected ? 'var(--masa-white)' : 'var(--masa-harbor)'}`,
            }} />
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
