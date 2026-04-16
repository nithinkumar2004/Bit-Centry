export default function StatusBadge({ status }) {
  const statusMap = {
    'Eligible': 'badge-eligible',
    'Not Eligible': 'badge-not-eligible',
    'Needs Manual Review': 'badge-review',
    'Pending': 'badge-pending',
    'uploaded': 'badge-info',
    'extracting': 'badge-pending',
    'ready': 'badge-eligible',
    'parsed': 'badge-eligible',
    'error': 'badge-not-eligible',
    'processing': 'badge-pending',
  }

  const dotMap = {
    'Eligible': '●',
    'Not Eligible': '●',
    'Needs Manual Review': '◐',
    'ready': '●',
    'parsed': '●',
    'error': '●',
  }

  const className = statusMap[status] || 'badge-pending'
  const dot = dotMap[status] || ''

  return (
    <span className={`badge ${className}`}>
      {dot && <span style={{ fontSize: '8px' }}>{dot}</span>}
      {status}
    </span>
  )
}
