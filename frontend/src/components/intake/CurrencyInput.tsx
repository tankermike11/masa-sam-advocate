import { useState } from 'react'

interface Props {
  value: number | null
  onChange: (v: number | null) => void
  optional?: boolean
}

export default function CurrencyInput({ value, onChange, optional }: Props) {
  const [unknown, setUnknown] = useState(false)

  const handleUnknown = () => {
    setUnknown(true)
    onChange(null)
  }

  return (
    <div style={{ marginTop: '0.5rem' }}>
      {!unknown && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--masa-horizon)', fontSize: '1.1rem' }}>$</span>
          <input
            type="number"
            min={0}
            step="0.01"
            placeholder="0.00"
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
            style={{
              border: '2px solid var(--masa-harbor-tint)', borderRadius: 'var(--radius-button)',
              padding: '0.6rem 0.8rem', fontSize: '1rem', width: '200px',
              outline: 'none', transition: 'border-color 0.15s',
            }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--masa-tide)')}
            onBlur={(e) => (e.target.style.borderColor = 'var(--masa-harbor-tint)')}
          />
        </div>
      )}
      {optional && !unknown && (
        <button
          onClick={handleUnknown}
          style={{
            marginTop: '0.4rem', background: 'none', color: 'var(--masa-harbor)',
            fontSize: '0.82rem', fontFamily: 'var(--font-body)', fontWeight: 400,
            padding: 0, border: 'none', textDecoration: 'underline', cursor: 'pointer',
          }}
        >
          I don't know / skip
        </button>
      )}
      {unknown && (
        <p style={{ color: 'var(--masa-harbor)', fontSize: '0.9rem', margin: '0.5rem 0' }}>
          Skipped — we'll work with what's available.{' '}
          <button
            onClick={() => setUnknown(false)}
            style={{ background: 'none', color: 'var(--masa-tide)', border: 'none', cursor: 'pointer', padding: 0, fontSize: '0.9rem' }}
          >
            Enter amount
          </button>
        </p>
      )}
    </div>
  )
}
