import { useState } from 'react'
import type { AnswerCard as AnswerCardType } from '../../lib/types'
import { fmtCurrency, WORKFLOW_LABELS } from '../../lib/utils'

interface Props { card: AnswerCardType }

export default function AnswerCard({ card }: Props) {
  const [showCitations, setShowCitations] = useState(false)
  const [showDisclaimer, setShowDisclaimer] = useState(false)

  return (
    <div style={{
      background: 'var(--masa-white)', borderRadius: 'var(--radius-card)',
      boxShadow: 'var(--shadow-card)', overflow: 'hidden',
      borderLeft: '4px solid var(--masa-tide)',
    }}>
      {/* Header */}
      <div style={{ background: 'var(--masa-horizon)', padding: '0.85rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--masa-white)', fontSize: '0.95rem' }}>
          SAM Assessment — {WORKFLOW_LABELS[card.workflow] ?? card.workflow}
        </span>
        {card.dollar_at_stake != null && (
          <span style={{ background: 'var(--masa-flare)', color: 'var(--masa-white)', borderRadius: 99, padding: '0.2rem 0.7rem', fontSize: '0.82rem', fontFamily: 'var(--font-heading)', fontWeight: 700 }}>
            {fmtCurrency(card.dollar_at_stake)} at stake
          </span>
        )}
      </div>

      <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
        {/* What We Found */}
        <Section title="What We Found" icon="📋" accent="var(--masa-tide)">
          <ul style={{ margin: 0, paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {card.what_we_found.map((item, i) => (
              <li key={i} style={{ fontSize: '0.92rem', lineHeight: 1.5 }}>{item}</li>
            ))}
          </ul>
        </Section>

        {/* What It Likely Means */}
        {card.what_it_likely_means.length > 0 && (
          <Section title="What It Likely Means" icon="💭" accent="var(--masa-harbor)" note="Interpretation — not legal advice">
            <ul style={{ margin: 0, paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {card.what_it_likely_means.map((item, i) => (
                <li key={i} style={{ fontSize: '0.92rem', lineHeight: 1.5 }}>{item}</li>
              ))}
            </ul>
          </Section>
        )}

        {/* What Needs Verification */}
        {card.what_needs_verification.length > 0 && (
          <Section title="What Still Needs Verification" icon="⚠" accent="#E65100" bg="#fff8f0">
            <ul style={{ margin: 0, paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {card.what_needs_verification.map((item, i) => (
                <li key={i} style={{ fontSize: '0.88rem', lineHeight: 1.5, color: '#5d3a1a' }}>{item}</li>
              ))}
            </ul>
          </Section>
        )}

        {/* Recommended Next Step */}
        <div style={{ background: 'var(--masa-horizon)', borderRadius: 'var(--radius-card)', padding: '1rem 1.1rem' }}>
          <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--masa-white)', fontSize: '0.85rem', marginBottom: '0.4rem', opacity: 0.8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Recommended Next Step
          </div>
          <p style={{ color: 'var(--masa-white)', margin: 0, fontSize: '0.95rem', lineHeight: 1.6 }}>
            {card.recommended_next_step}
          </p>
        </div>

        {/* Citations toggle */}
        {card.citations.length > 0 && (
          <div>
            <button
              onClick={() => setShowCitations((s) => !s)}
              style={{ background: 'none', color: 'var(--masa-tide)', border: 'none', padding: 0, fontSize: '0.83rem', fontFamily: 'var(--font-body)', cursor: 'pointer' }}
            >
              {showCitations ? '▼' : '▶'} {card.citations.length} citation{card.citations.length !== 1 ? 's' : ''}
            </button>
            {showCitations && (
              <ul style={{ margin: '0.4rem 0 0', paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                {card.citations.map((c, i) => (
                  <li key={i} style={{ fontSize: '0.8rem', color: 'var(--masa-harbor)' }}>
                    {c.publisher ?? c.source_id}
                    {c.canonical_url && (
                      <> — <a href={c.canonical_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--masa-tide)' }}>source</a></>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* Disclaimer toggle */}
        <div>
          <button
            onClick={() => setShowDisclaimer((s) => !s)}
            style={{ background: 'none', color: 'var(--masa-harbor)', border: 'none', padding: 0, fontSize: '0.78rem', fontFamily: 'var(--font-body)', cursor: 'pointer' }}
          >
            {showDisclaimer ? '▼' : '▶'} Disclaimer
          </button>
          {showDisclaimer && (
            <p style={{ fontSize: '0.78rem', color: 'var(--masa-harbor)', margin: '0.3rem 0 0', lineHeight: 1.5 }}>
              {card.disclaimer}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function Section({ title, icon, accent, note, bg, children }: {
  title: string; icon: string; accent: string; note?: string; bg?: string; children: React.ReactNode
}) {
  return (
    <div style={{ background: bg ?? 'transparent' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginBottom: '0.5rem' }}>
        <span>{icon}</span>
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '0.88rem', color: accent }}>{title}</span>
        {note && <span style={{ fontSize: '0.75rem', color: 'var(--masa-harbor)', fontStyle: 'italic' }}>({note})</span>}
      </div>
      {children}
    </div>
  )
}
