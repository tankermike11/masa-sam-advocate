import { useState, useEffect } from 'react'

interface PreconditionCounts {
  sources: number
  nsa_rules: number
  ambulance_fee_schedule: number
}

interface HealthResponse {
  status: string
  version: string
  pilot_db_path: string
  app_db_path: string
  precondition_tables: PreconditionCounts
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((res) => {
        if (!res.ok) throw new Error(`/health returned ${res.status}`)
        return res.json() as Promise<HealthResponse>
      })
      .then(setHealth)
      .catch((e: Error) => setError(e.message))
  }, [])

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 600, margin: '40px auto', padding: '0 20px' }}>
      <h1>SAM — MASA Medical Bill Advocate</h1>
      <p>Phase 0 scaffold. Application interface will be built in Phase 1+.</p>

      <h2>System Status</h2>
      {error && (
        <div style={{ color: 'red', border: '1px solid red', padding: 12, borderRadius: 4 }}>
          Backend unavailable: {error}
        </div>
      )}
      {health && (
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <tbody>
            <tr>
              <td style={tdStyle}><strong>Status</strong></td>
              <td style={tdStyle}>{health.status}</td>
            </tr>
            <tr>
              <td style={tdStyle}><strong>Version</strong></td>
              <td style={tdStyle}>{health.version}</td>
            </tr>
            <tr>
              <td style={tdStyle}><strong>sources</strong></td>
              <td style={tdStyle}>{health.precondition_tables.sources} rows</td>
            </tr>
            <tr>
              <td style={tdStyle}><strong>nsa_rules</strong></td>
              <td style={tdStyle}>{health.precondition_tables.nsa_rules} rows</td>
            </tr>
            <tr>
              <td style={tdStyle}><strong>ambulance_fee_schedule</strong></td>
              <td style={tdStyle}>{health.precondition_tables.ambulance_fee_schedule} rows</td>
            </tr>
          </tbody>
        </table>
      )}
      {!health && !error && <p>Checking backend...</p>}
    </div>
  )
}

const tdStyle: React.CSSProperties = {
  border: '1px solid #ddd',
  padding: '8px 12px',
}

export default App
