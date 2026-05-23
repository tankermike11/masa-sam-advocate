interface Props {
  value: boolean | null
  onChange: (v: boolean) => void
}

export default function YesNoToggle({ value, onChange }: Props) {
  return (
    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
      {([true, false] as const).map((v) => (
        <button
          key={String(v)}
          onClick={() => onChange(v)}
          style={{
            padding: '0.6rem 1.5rem',
            background: value === v ? 'var(--masa-horizon)' : 'var(--masa-white)',
            color: value === v ? 'var(--masa-white)' : 'var(--masa-horizon)',
            border: `2px solid var(--masa-horizon)`,
            borderRadius: 'var(--radius-button)',
            fontFamily: 'var(--font-heading)',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s',
          }}
        >
          {v ? 'Yes' : 'No'}
        </button>
      ))}
    </div>
  )
}
