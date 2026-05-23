interface Props {
  value: string | null
  onChange: (v: string) => void
}

const OPTIONS = [
  { label: 'In-network', value: 'in_network', color: 'var(--masa-tide)' },
  { label: 'Out-of-network', value: 'out_of_network', color: 'var(--masa-flare)' },
  { label: 'Not sure', value: 'unknown', color: 'var(--masa-harbor)' },
]

export default function NetworkStatusPicker({ value, onChange }: Props) {
  return (
    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
      {OPTIONS.map((opt) => {
        const selected = value === opt.value
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            style={{
              padding: '0.6rem 1.1rem', borderRadius: 'var(--radius-button)',
              border: `2px solid ${selected ? opt.color : 'var(--masa-harbor-tint)'}`,
              background: selected ? opt.color : 'var(--masa-white)',
              color: selected ? 'var(--masa-white)' : 'var(--masa-body)',
              fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '0.88rem',
              cursor: 'pointer', transition: 'all 0.15s',
            }}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
