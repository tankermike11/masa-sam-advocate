import { useState } from 'react'
import type { GeneratedDocument } from '../../lib/types'

const DOC_LABELS: Record<string, string> = {
  itemized_bill_request: 'Itemized Bill Request Letter',
  internal_appeal:       'First-Level Internal Appeal Letter',
  balance_bill_dispute:  'Balance-Bill Dispute Letter',
  ppdr_initiation:       'PPDR Initiation Summary',
}

interface Props { documents: Record<string, GeneratedDocument> }

export default function DocumentViewer({ documents }: Props) {
  const [open, setOpen] = useState<string | null>(null)

  const entries = Object.entries(documents)
  if (entries.length === 0) return null

  const copyText = (text: string) => navigator.clipboard.writeText(text).catch(() => {})

  const downloadText = (text: string, name: string) => {
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `${name}.txt`; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <h3 style={{ fontFamily: 'var(--font-heading)', color: 'var(--masa-horizon)', fontSize: '1rem', margin: 0 }}>
        Generated Documents
      </h3>

      {/* Counsel banner */}
      <div style={{
        background: '#fff3e0', border: '1px solid #ffb74d', borderRadius: 'var(--radius-card)',
        padding: '0.65rem 0.9rem', fontSize: '0.83rem', color: '#5d3a1a',
      }}>
        ⚠ These documents require counsel review before use. Complete all <strong>[BRACKETED]</strong> fields before sending.
      </div>

      {entries.map(([key, doc]) => {
        const label = DOC_LABELS[key] ?? key
        const isOpen = open === key
        return (
          <div key={key} style={{ background: 'var(--masa-white)', borderRadius: 'var(--radius-card)', boxShadow: 'var(--shadow-card)', overflow: 'hidden' }}>
            <button
              onClick={() => setOpen(isOpen ? null : key)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '0.85rem 1rem', background: 'none', border: 'none', cursor: 'pointer',
                borderBottom: isOpen ? '1px solid var(--masa-harbor-tint)' : 'none',
              }}
            >
              <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--masa-horizon)', fontSize: '0.92rem' }}>
                📄 {label}
              </span>
              <span style={{ color: 'var(--masa-harbor)', fontSize: '0.85rem' }}>{isOpen ? '▼' : '▶'}</span>
            </button>

            {isOpen && (
              <div style={{ padding: '1rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <button onClick={() => copyText(doc.content)} className="btn-secondary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.8rem' }}>Copy</button>
                  <button onClick={() => downloadText(doc.content, key)} className="btn-secondary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.8rem' }}>Download .txt</button>
                </div>
                <pre style={{
                  background: 'var(--masa-harbor-tint)', borderRadius: 'var(--radius-card)',
                  padding: '1rem', fontSize: '0.8rem', lineHeight: 1.6, whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word', maxHeight: 320, overflowY: 'auto', margin: 0,
                  fontFamily: 'monospace',
                }}>
                  {doc.content}
                </pre>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
