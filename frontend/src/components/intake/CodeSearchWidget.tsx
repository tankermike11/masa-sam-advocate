import { useState, useCallback, useRef } from 'react'
import { api } from '../../lib/api'
import type { CodeEntry, CodeSearchResult } from '../../lib/types'

interface Props {
  value: CodeEntry[]
  onChange: (codes: CodeEntry[]) => void
}

function detectCodeType(q: string): string | undefined {
  const s = q.trim().toUpperCase()
  if (/^\d{5}$/.test(s)) return 'CPT'
  if (/^[A-Z]\d{4}$/.test(s)) return 'HCPCS'
  if (/^[A-Z]\d{2}/.test(s) && s.length >= 3 && s.length <= 7) return 'ICD10CM'
  if (/^\d{7}[A-Z0-9]?$/.test(s)) return 'ICD10PCS'
  if (/^\d{1,3}$/.test(s)) return 'CARC'
  return undefined
}

export default function CodeSearchWidget({ value, onChange }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<CodeSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const search = useCallback((q: string) => {
    if (!q.trim()) { setResults([]); return }
    const detectedType = detectCodeType(q)
    setLoading(true)
    api.searchCodes(q, detectedType)
      .then(setResults)
      .catch(() => setResults([]))
      .finally(() => setLoading(false))
  }, [])

  const handleInput = (q: string) => {
    setQuery(q)
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => search(q), 300)
  }

  const addCode = (r: CodeSearchResult) => {
    const entry: CodeEntry = { code_type: r.code_type, code: r.code }
    if (!value.find((e) => e.code === r.code && e.code_type === r.code_type)) {
      onChange([...value, entry])
    }
    setQuery('')
    setResults([])
  }

  const removeCode = (idx: number) => {
    const next = [...value]
    next.splice(idx, 1)
    onChange(next)
  }

  return (
    <div style={{ marginTop: '0.5rem' }}>
      {/* Chips */}
      {value.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.5rem' }}>
          {value.map((e, i) => (
            <span key={i} className="chip">
              {e.code_type} {e.code}
              <button
                onClick={() => removeCode(i)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'var(--masa-horizon)', fontSize: '0.9rem', lineHeight: 1 }}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search input */}
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => handleInput(e.target.value)}
          placeholder="Type a code (e.g. A0427) or description…"
          style={{
            width: '100%', maxWidth: 360,
            border: '2px solid var(--masa-harbor-tint)', borderRadius: 'var(--radius-button)',
            padding: '0.6rem 0.8rem', fontSize: '0.95rem',
          }}
          onFocus={(e) => (e.target.style.borderColor = 'var(--masa-tide)')}
          onBlur={(e) => (e.target.style.borderColor = 'var(--masa-harbor-tint)')}
        />
        {loading && (
          <span style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--masa-harbor)', fontSize: '0.8rem' }}>
            …
          </span>
        )}

        {results.length > 0 && (
          <div style={{
            position: 'absolute', top: '110%', left: 0, zIndex: 100,
            background: 'var(--masa-white)', border: '1px solid var(--masa-harbor-tint)',
            borderRadius: 'var(--radius-card)', boxShadow: 'var(--shadow-card)',
            maxHeight: 220, overflowY: 'auto', width: '100%', maxWidth: 400,
          }}>
            {results.map((r, i) => (
              <button
                key={i}
                onMouseDown={() => addCode(r)}
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  padding: '0.55rem 0.8rem', background: 'none', border: 'none',
                  cursor: 'pointer', fontFamily: 'var(--font-body)', borderBottom: i < results.length - 1 ? '1px solid var(--masa-harbor-tint)' : 'none',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--masa-harbor-tint)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
              >
                <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--masa-horizon)' }}>{r.code_type} {r.code}</span>
                {r.fallback ? (
                  <span style={{ marginLeft: '0.5rem', fontSize: '0.78rem', color: 'var(--masa-harbor)' }}>CPT — description not available (AMA licensed)</span>
                ) : (
                  <span style={{ marginLeft: '0.5rem', fontSize: '0.82rem', color: 'var(--masa-body)' }}>{r.description ?? r.short_description}</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
      <p style={{ fontSize: '0.78rem', color: 'var(--masa-harbor)', marginTop: '0.3rem' }}>Optional — skip if codes aren't on your bill</p>
    </div>
  )
}
