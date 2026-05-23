interface Props { severity: string; size?: 'sm' | 'md' }

const MAP: Record<string, string> = {
  minor: 'badge-minor', moderate: 'badge-moderate',
  high: 'badge-high', catastrophic: 'badge-catastrophic',
}

export default function SeverityBadge({ severity, size = 'md' }: Props) {
  const cls = MAP[severity] ?? 'badge-unknown'
  const style = size === 'sm' ? { fontSize: '0.72rem', padding: '0.15rem 0.5rem' } : {}
  return <span className={`badge ${cls}`} style={style}>{severity}</span>
}
