interface Props { message?: string }

export default function LoadingSpinner({ message = 'SAM is reviewing your case…' }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '2rem' }}>
      <div style={{
        width: 40, height: 40, border: '3px solid var(--masa-harbor-tint)',
        borderTop: '3px solid var(--masa-tide)', borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <p style={{ color: 'var(--masa-harbor)', fontFamily: 'var(--font-body)', margin: 0 }}>{message}</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
