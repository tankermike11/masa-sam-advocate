import type { StepOption } from '../../lib/intake-steps'

interface Props {
  options: StepOption[]
  value: string | null
  onChange: (v: string) => void
}

export default function CardPicker({ options, value, onChange }: Props) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
      gap: '0.75rem',
      marginTop: '0.5rem',
    }}>
      {options.map((opt) => {
        const selected = value === opt.value
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            style={{
              background: selected ? 'var(--masa-horizon)' : 'var(--masa-white)',
              color: selected ? 'var(--masa-white)' : 'var(--masa-body)',
              border: `2px solid ${selected ? 'var(--masa-horizon)' : 'var(--masa-harbor-tint)'}`,
              borderRadius: 'var(--radius-card)',
              padding: '0.85rem 1rem',
              textAlign: 'left',
              cursor: 'pointer',
              transition: 'all 0.15s',
              boxShadow: selected ? 'var(--shadow-card)' : 'none',
            }}
          >
            <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '0.9rem', marginBottom: opt.description ? '0.3rem' : 0 }}>
              {opt.label}
            </div>
            {opt.description && (
              <div style={{ fontSize: '0.78rem', opacity: selected ? 0.85 : 0.65, lineHeight: 1.4 }}>
                {opt.description}
              </div>
            )}
          </button>
        )
      })}
    </div>
  )
}
