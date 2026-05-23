import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { SCENARIOS } from '../lib/scenarios'

export default function ScenariosPage() {
  const nav = useNavigate()
  const [expanded, setExpanded] = useState<string | null>(null)

  const run = (id: string) => {
    const scenario = SCENARIOS.find((s) => s.id === id)
    if (scenario) nav('/case', { state: { prefill: scenario.intake } })
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ background: 'var(--masa-horizon)', padding: '1rem 2rem', display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <a href="/" style={{ color: 'var(--masa-white)', opacity: 0.7, fontSize: '0.85rem', textDecoration: 'none' }}>← Back</a>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 30, height: 30, background: 'var(--masa-tide)', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'white', fontSize: '1rem' }}>+</div>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--masa-white)', fontSize: '1rem' }}>MASA Access — Demo Scenarios</span>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: '2rem 1.25rem', width: '100%' }}>
        <h2 style={{ fontSize: '1.4rem', marginBottom: '0.4rem' }}>Pre-Built Scenarios</h2>
        <p style={{ color: 'var(--masa-harbor)', marginBottom: '1.5rem', fontSize: '0.93rem' }}>
          Each scenario pre-fills the intake and runs straight to the SAM assessment. Click <strong>Run this scenario</strong> to see the engine in action.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {SCENARIOS.map((s) => (
            <div key={s.id} style={{ background: 'var(--masa-white)', borderRadius: 'var(--radius-card)', boxShadow: 'var(--shadow-card)', overflow: 'hidden' }}>
              {/* Card header */}
              <div style={{ padding: '1.1rem 1.25rem', borderBottom: expanded === s.id ? '1px solid var(--masa-harbor-tint)' : 'none' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '1rem', marginBottom: '0.3rem' }}>{s.title}</h3>
                    <p style={{ color: 'var(--masa-body)', fontSize: '0.88rem', margin: '0 0 0.5rem' }}>{s.description}</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                      {s.tags.map((t) => <span key={t} className="chip" style={{ fontSize: '0.75rem' }}>{t}</span>)}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0, alignItems: 'center' }}>
                    <button
                      onClick={() => setExpanded(expanded === s.id ? null : s.id)}
                      style={{ background: 'none', border: '1px solid var(--masa-harbor-tint)', borderRadius: 'var(--radius-button)', padding: '0.4rem 0.75rem', fontSize: '0.8rem', color: 'var(--masa-harbor)', cursor: 'pointer' }}
                    >
                      {expanded === s.id ? 'Less' : 'Details'}
                    </button>
                    <button onClick={() => run(s.id)} className="btn-primary" style={{ fontSize: '0.88rem', padding: '0.5rem 1.1rem' }}>
                      Run this scenario →
                    </button>
                  </div>
                </div>
              </div>

              {/* Expandable detail */}
              {expanded === s.id && (
                <div style={{ padding: '1rem 1.25rem', background: '#f9f8fb', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div>
                    <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '0.82rem', color: 'var(--masa-horizon)', marginBottom: '0.35rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      What to look for
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '1.1rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      {s.lookFor.map((l, i) => <li key={i} style={{ fontSize: '0.85rem', color: 'var(--masa-body)' }}>{l}</li>)}
                    </ul>
                  </div>
                  <div>
                    <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '0.82rem', color: 'var(--masa-horizon)', marginBottom: '0.35rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Intake data
                    </div>
                    <pre style={{ background: 'var(--masa-white)', border: '1px solid var(--masa-harbor-tint)', borderRadius: 'var(--radius-card)', padding: '0.75rem', fontSize: '0.75rem', overflow: 'auto', maxHeight: 200, margin: 0, fontFamily: 'monospace' }}>
                      {JSON.stringify(s.intake, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
