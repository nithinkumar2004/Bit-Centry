import { useState, useEffect } from 'react'
import { Plus, Users, Trash2, Eye, AlertTriangle } from 'lucide-react'
import { fetchBidders, fetchTenders, uploadBidder, deleteBidder } from '../api/client'
import Modal from '../components/Modal'
import FileUpload from '../components/FileUpload'
import StatusBadge from '../components/StatusBadge'

export default function Bidders({ addToast }) {
  const [bidders, setBidders] = useState([])
  const [tenders, setTenders] = useState([])
  const [loading, setLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [form, setForm] = useState({ name: '', tenderId: '' })
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [bidderData, tenderData] = await Promise.all([
        fetchBidders(),
        fetchTenders()
      ])
      setBidders(bidderData.bidders || [])
      setTenders(tenderData.tenders || [])
    } catch (err) {
      addToast('Failed to load data', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!form.name.trim() || !form.tenderId || files.length === 0) {
      addToast('Please fill all fields and select files', 'error')
      return
    }
    setUploading(true)
    try {
      const result = await uploadBidder(form.name, form.tenderId, files)
      addToast(`Bidder "${form.name}" uploaded successfully!`, 'success')
      if (result.low_confidence) {
        addToast('⚠️ Low OCR confidence detected — results may need manual review', 'info')
      }
      setShowUpload(false)
      setForm({ name: '', tenderId: '' })
      setFiles([])
      loadData()
    } catch (err) {
      addToast('Upload failed: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this bidder?')) return
    try {
      await deleteBidder(id)
      addToast('Bidder deleted', 'info')
      loadData()
    } catch (err) {
      addToast('Delete failed', 'error')
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <div className="loading-text">Loading bidders...</div>
      </div>
    )
  }

  return (
    <div className="fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Bidders</h1>
          <p className="page-subtitle">Upload and manage bidder documents</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
          <Plus size={18} /> Add Bidder
        </button>
      </div>

      {bidders.length === 0 ? (
        <div className="card empty-state">
          <Users className="empty-state-icon" size={64} />
          <div className="empty-state-title">No bidders yet</div>
          <div className="empty-state-text">Upload bidder documents to start evaluating</div>
          <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
            <Plus size={18} /> Add Bidder
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
          {bidders.map(bidder => (
            <div key={bidder.id} className="card slide-up">
              <div className="flex items-center justify-between mb-16">
                <div>
                  <div className="font-bold" style={{ fontSize: 16 }}>{bidder.name}</div>
                  <div className="text-sm text-muted mt-4">{bidder.documents_count} document(s)</div>
                </div>
                <div className="flex gap-8">
                  <StatusBadge status={bidder.status} />
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(bidder.id)} style={{ padding: '4px 8px' }}>
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              
              {/* Extracted Data */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div style={{ padding: 12, background: 'rgba(59, 130, 246, 0.06)', borderRadius: 10 }}>
                  <div className="text-sm text-muted" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 }}>Turnover</div>
                  <div className="font-bold" style={{ color: 'var(--accent-blue)', fontSize: 18 }}>
                    {bidder.turnover ? `₹${bidder.turnover} Cr` : '—'}
                  </div>
                </div>
                <div style={{ padding: 12, background: 'rgba(139, 92, 246, 0.06)', borderRadius: 10 }}>
                  <div className="text-sm text-muted" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 }}>Projects</div>
                  <div className="font-bold" style={{ color: 'var(--accent-purple)', fontSize: 18 }}>
                    {bidder.project_count ?? '—'}
                  </div>
                </div>
              </div>

              {/* Certifications */}
              <div className="mt-12">
                <div className="text-sm text-muted mb-8" style={{ fontSize: 11, textTransform: 'uppercase' }}>Certifications</div>
                <div className="flex flex-wrap gap-8">
                  {bidder.certifications?.length > 0
                    ? bidder.certifications.map((c, i) => (
                        <span key={i} className="badge badge-info">{c}</span>
                      ))
                    : <span className="text-muted text-sm">None found</span>
                  }
                </div>
              </div>

              {/* Confidence */}
              <div className="mt-12">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted">OCR Confidence</span>
                  <span className="text-sm font-semibold" style={{
                    color: bidder.confidence >= 0.8 ? 'var(--status-eligible)' :
                           bidder.confidence >= 0.5 ? 'var(--status-review)' : 'var(--status-not-eligible)'
                  }}>
                    {(bidder.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="confidence-bar">
                  <div
                    className={`confidence-bar-fill ${
                      bidder.confidence >= 0.8 ? 'high' :
                      bidder.confidence >= 0.5 ? 'medium' : 'low'
                    }`}
                    style={{ width: `${bidder.confidence * 100}%` }}
                  />
                </div>
                {bidder.confidence < 0.7 && (
                  <div className="flex items-center gap-4 mt-8" style={{ color: 'var(--status-review)', fontSize: 12 }}>
                    <AlertTriangle size={12} />
                    <span>Low confidence — may need manual review</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <Modal isOpen={showUpload} onClose={() => setShowUpload(false)} title="Add Bidder">
        <div className="form-group">
          <label className="form-label">Bidder Name / Company</label>
          <input
            className="form-input"
            placeholder="E.g., ABC Constructions Pvt Ltd"
            value={form.name}
            onChange={e => setForm({ ...form, name: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Associated Tender</label>
          <select
            className="form-input"
            value={form.tenderId}
            onChange={e => setForm({ ...form, tenderId: e.target.value })}
          >
            <option value="">Select a tender...</option>
            {tenders.map(t => (
              <option key={t.id} value={t.id}>{t.title}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Documents (Multiple Allowed)</label>
          <FileUpload
            onFilesSelected={setFiles}
            multiple={true}
            accept=".pdf,.png,.jpg,.jpeg"
          />
        </div>
        <div className="flex gap-12" style={{ justifyContent: 'flex-end', marginTop: 24 }}>
          <button className="btn btn-secondary" onClick={() => setShowUpload(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
            {uploading
              ? <><div className="spinner spinner-sm" /> Processing...</>
              : <><Plus size={16} /> Upload & Parse</>
            }
          </button>
        </div>
      </Modal>
    </div>
  )
}
