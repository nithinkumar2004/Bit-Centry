import { useState, useEffect } from 'react'
import {
  Shield, ShieldCheck, ShieldAlert,
  Upload, FileText, CheckCircle2, Trash2, Download,
  RefreshCw, Filter
} from 'lucide-react'
import { fetchAuditLogs, verifyAuditChain } from '../api/client'

export default function AuditLog({ addToast }) {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [chainStatus, setChainStatus] = useState(null)
  const [verifying, setVerifying] = useState(false)
  const [filter, setFilter] = useState('')
  const [page, setPage] = useState(0)
  const limit = 30

  useEffect(() => { loadLogs() }, [page, filter])

  const loadLogs = async () => {
    setLoading(true)
    try {
      const data = await fetchAuditLogs(
        filter || null,
        null,
        page * limit,
        limit
      )
      setLogs(data.logs || [])
      setTotal(data.total || 0)
    } catch (err) {
      addToast('Failed to load audit logs', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async () => {
    setVerifying(true)
    try {
      const result = await verifyAuditChain()
      setChainStatus(result)
      if (result.is_valid) {
        addToast(`✅ Audit chain verified! ${result.total_entries} entries intact.`, 'success')
      } else {
        addToast('⚠️ Chain integrity violation detected!', 'error')
      }
    } catch (err) {
      addToast('Verification failed', 'error')
    } finally {
      setVerifying(false)
    }
  }

  const actionIcon = (action) => {
    const map = {
      'UPLOAD': <Upload size={14} />,
      'EXTRACT': <FileText size={14} />,
      'PARSE': <FileText size={14} />,
      'EVALUATE': <CheckCircle2 size={14} />,
      'DELETE': <Trash2 size={14} />,
      'EXPORT': <Download size={14} />,
    }
    return map[action] || <Shield size={14} />
  }

  const actionClass = (action) => {
    const map = {
      'UPLOAD': 'upload',
      'EXTRACT': 'extract',
      'PARSE': 'upload',
      'EVALUATE': 'evaluate',
      'DELETE': 'delete',
      'EXPORT': 'export',
    }
    return map[action] || ''
  }

  const formatTimestamp = (ts) => {
    try {
      return new Date(ts).toLocaleString()
    } catch {
      return ts
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Audit Log</h1>
          <p className="page-subtitle">Tamper-evident, hash-chained audit trail</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleVerify}
          disabled={verifying}
        >
          {verifying
            ? <><div className="spinner spinner-sm" /> Verifying...</>
            : <><ShieldCheck size={18} /> Verify Chain</>
          }
        </button>
      </div>

      {/* Chain Status Banner */}
      {chainStatus && (
        <div className={`card mb-24 ${chainStatus.is_valid ? '' : ''}`} style={{
          borderLeft: `4px solid ${chainStatus.is_valid ? 'var(--status-eligible)' : 'var(--status-not-eligible)'}`,
          background: chainStatus.is_valid
            ? 'rgba(16, 185, 129, 0.06)'
            : 'rgba(244, 63, 94, 0.06)'
        }}>
          <div className="flex items-center gap-12">
            {chainStatus.is_valid
              ? <ShieldCheck size={24} style={{ color: 'var(--status-eligible)' }} />
              : <ShieldAlert size={24} style={{ color: 'var(--status-not-eligible)' }} />
            }
            <div>
              <div className="font-bold" style={{
                color: chainStatus.is_valid ? 'var(--status-eligible)' : 'var(--status-not-eligible)'
              }}>
                {chainStatus.is_valid ? 'Chain Integrity Verified ✓' : 'Chain Integrity BROKEN ✕'}
              </div>
              <div className="text-sm text-muted">
                {chainStatus.total_entries} entries in the chain
                {chainStatus.broken_at && ` — Broken at entry #${chainStatus.broken_at.entry_number}`}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="card mb-24">
        <div className="flex items-center gap-16">
          <Filter size={18} className="text-muted" />
          <select
            className="form-input"
            style={{ maxWidth: 200 }}
            value={filter}
            onChange={e => { setFilter(e.target.value); setPage(0) }}
          >
            <option value="">All Types</option>
            <option value="tender">Tenders</option>
            <option value="bidder">Bidders</option>
            <option value="evaluation">Evaluations</option>
          </select>
          <span className="text-sm text-muted">{total} total entries</span>
          <button className="btn btn-sm btn-secondary" onClick={loadLogs}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Log Entries */}
      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
          <div className="loading-text">Loading audit logs...</div>
        </div>
      ) : logs.length === 0 ? (
        <div className="card empty-state">
          <Shield className="empty-state-icon" size={64} />
          <div className="empty-state-title">No audit logs yet</div>
          <div className="empty-state-text">Actions will be recorded here automatically</div>
        </div>
      ) : (
        <>
          <div className="table-container card" style={{ padding: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Input Hash</th>
                  <th>Output Hash</th>
                  <th>Prev Hash</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log, i) => (
                  <tr key={log.id || i}>
                    <td>
                      <div className="flex items-center gap-8">
                        <div className={`activity-icon ${actionClass(log.action)}`} style={{ width: 28, height: 28 }}>
                          {actionIcon(log.action)}
                        </div>
                        <span className="font-semibold">{log.action}</span>
                      </div>
                    </td>
                    <td>
                      <div className="text-sm">
                        <span className="badge badge-info" style={{ fontSize: 11 }}>{log.entity_type}</span>
                      </div>
                      <div className="hash-display mt-4" style={{ maxWidth: 140, fontSize: 10 }}>
                        {log.entity_id}
                      </div>
                    </td>
                    <td>
                      <div className="hash-display">{log.input_hash?.slice(0, 16)}...</div>
                    </td>
                    <td>
                      <div className="hash-display">{log.output_hash?.slice(0, 16)}...</div>
                    </td>
                    <td>
                      <div className="hash-display">
                        {log.prev_hash === 'GENESIS' ? '🏁 GENESIS' : `${log.prev_hash?.slice(0, 12)}...`}
                      </div>
                    </td>
                    <td className="text-sm text-muted">{formatTimestamp(log.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {total > limit && (
            <div className="flex items-center justify-center gap-12 mt-24">
              <button
                className="btn btn-sm btn-secondary"
                disabled={page === 0}
                onClick={() => setPage(p => p - 1)}
              >
                Previous
              </button>
              <span className="text-sm text-muted">
                Page {page + 1} of {Math.ceil(total / limit)}
              </span>
              <button
                className="btn btn-sm btn-secondary"
                disabled={(page + 1) * limit >= total}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
