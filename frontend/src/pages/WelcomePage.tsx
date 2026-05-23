import { useNavigate } from 'react-router-dom'

export default function WelcomePage() {
  const nav = useNavigate()
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Hero header */}
      <div style={{ background: 'var(--masa-horizon)', padding: '1.5rem 2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          width: 36, height: 36, background: 'var(--masa-tide)', borderRadius: 6,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'white', fontSize: '1.2rem',
        }}>+</div>
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--masa-white)', fontSize: '1.15rem', letterSpacing: '0.02em' }}>
          MASA Access
        </span>
      </div>

      {/* Main content */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        padding: '3rem 1.5rem', textAlign: 'center',
      }}>
        <div style={{
          background: 'var(--masa-tide)', width: 64, height: 64, borderRadius: 16,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: '1.5rem', boxShadow: '0 4px 16px rgba(0,113,206,0.35)',
        }}>
          <span style={{ fontSize: '2rem' }}>🛡</span>
        </div>

        <h1 style={{ fontSize: 'clamp(1.8rem, 5vw, 2.8rem)', color: 'var(--masa-horizon)', marginBottom: '0.5rem', lineHeight: 1.2 }}>
          Meet SAM
        </h1>
        <p style={{ fontSize: '1.1rem', color: 'var(--masa-harbor)', maxWidth: 520, marginBottom: '0.75rem', lineHeight: 1.6 }}>
          Your MASA Medical Bill Advocate. SAM reviews your bill, explains your rights, and tells you exactly what to do next.
        </p>
        <p style={{ fontSize: '0.85rem', color: 'var(--masa-harbor)', maxWidth: 480, marginBottom: '2.5rem' }}>
          SAM provides information and self-help guidance — not legal or insurance advice.
        </p>

        <button
          onClick={() => nav('/case')}
          className="btn-horizon"
          style={{ fontSize: '1.05rem', padding: '0.9rem 2.5rem', boxShadow: '0 4px 12px rgba(35,8,113,0.25)' }}
        >
          Help me with a medical bill
        </button>

        {/* Feature pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', justifyContent: 'center', marginTop: '2rem', maxWidth: 480 }}>
          {['Ambulance & surprise bills', 'Insurance denials', 'Bill errors', 'Collections', 'Document generation'].map((f) => (
            <span key={f} className="chip" style={{ fontSize: '0.82rem' }}>{f}</span>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div style={{ padding: '1rem 2rem', borderTop: '1px solid var(--masa-harbor-tint)', display: 'flex', justifyContent: 'center', gap: '1.5rem' }}>
        <a href="/scenarios" style={{ fontSize: '0.82rem', color: 'var(--masa-harbor)' }}>Scenarios</a>
        <a href="/admin" style={{ fontSize: '0.82rem', color: 'var(--masa-harbor)' }}>Advocate Login</a>
      </div>
    </div>
  )
}
