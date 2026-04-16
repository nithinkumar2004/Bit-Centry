import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FileText, Sparkles, Trash2, Eye, Search } from 'lucide-react'
import { fetchTenders, uploadTender, extractCriteria, deleteTender } from '../api/client'
import Modal from '../components/Modal'
import FileUpload from '../components/FileUpload'
import StatusBadge from '../components/StatusBadge'

export default function Tenders({ addToast }) {
  const [tenders, setTenders] = useState([])
  const [loading, setLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadFile, setUploadFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [extracting, setExtracting] = useState({})
  const navigate = useNavigate()

  useEffect(() => { loadTenders() }, [])

  const loadTenders = async () => {
    try {
      const data = await fetchTenders()
      setTenders(data.tenders || [])
    } catch (err) {
      addToast('Failed to load tenders', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!uploadTitle.trim() || !uploadFile) {
      addToast('Please provide a title and file', 'error')
      return
    }
    setUploading(true)
    try {
      await uploadTender(uploadTitle, uploadFile)
      addToast('Tender uploaded successfully!', 'success')
      setShowUpload(false)
      setUploadTitle('')
      setUploadFile(null)
      loadTenders()
    } catch (err) {
      addToast('Upload failed: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setUploading(false)
    }
  }

  const handleExtract = async (id) => {
    setExtracting(prev => ({ ...prev, [id]: true }))
    try {
      const result = await extractCriteria(id)
      addToast(`Extracted ${result.count} criteria!`, 'success')
      loadTenders()
    } catch (err) {
      addToast('Extraction failed: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setExtracting(prev => ({ ...prev, [id]: false }))
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this tender?')) return
    try {
      await deleteTender(id)
      addToast('Tender deleted', 'info')
      loadTenders()
    } catch (err) {
      addToast('Delete failed', 'error')
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <div className="loading-text">Loading tenders...</div>
      </div>
    )
  }

  return (
    <div className="fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Tenders</h1>
          <p className="page-subtitle">Upload and manage tender documents</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
          <Plus size={18} /> Upload Tender
        </button>
      </div>

      {tenders.length === 0 ? (
        <div className="card empty-state">
          <FileText className="empty-state-icon" size={64} />
          <div className="empty-state-title">No tenders yet</div>
          <div className="empty-state-text">Upload your first tender document to get started</div>
          <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
            <Plus size={18} /> Upload Tender
          </button>
        </div>
      ) : (
        <div className="table-container card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Criteria</th>
                <th>OCR Confidence</th>
                <th>Created</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tenders.map(tender => (
                <tr key={tender.id}>
                  <td>
                    <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {tender.title}
                    </div>
                  </td>
                  <td><StatusBadge status={tender.status} /></td>
                  <td>
                    <span className="badge badge-info">{tender.criteria_count} criteria</span>
                  </td>
                  <td>
                    <div className="flex items-center gap-8">
                      <span>{(tender.ocr_confidence * 100).toFixed(0)}%</span>
                      <div className="confidence-bar" style={{ width: 60 }}>
                        <div
                          className={`confidence-bar-fill ${
                            tender.ocr_confidence >= 0.8 ? 'high' : 
                            tender.ocr_confidence >= 0.5 ? 'medium' : 'low'
                          }`}
                          style={{ width: `${tender.ocr_confidence * 100}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="text-sm text-muted">
                    {tender.created_at ? new Date(tender.created_at).toLocaleDateString() : ''}
                  </td>
                  <td>
                    <div className="flex items-center gap-8" style={{ justifyContent: 'flex-end' }}>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => navigate(`/tenders/${tender.id}`)}
                        title="View details"
                      >
                        <Eye size={14} />
                      </button>
                      {tender.status === 'uploaded' && (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => handleExtract(tender.id)}
                          disabled={extracting[tender.id]}
                          title="Extract criteria"
                        >
                          {extracting[tender.id] ? (
                            <div className="spinner spinner-sm" />
                          ) : (
                            <><Sparkles size={14} /> Extract</>
                          )}
                        </button>
                      )}
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDelete(tender.id)}
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Upload Modal */}
      <Modal isOpen={showUpload} onClose={() => setShowUpload(false)} title="Upload Tender Document">
        <div className="form-group">
          <label className="form-label">Tender Title</label>
          <input
            className="form-input"
            type="text"
            placeholder="E.g., CRPF Construction Tender 2024"
            value={uploadTitle}
            onChange={e => setUploadTitle(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Document File</label>
          <FileUpload
            onFilesSelected={files => setUploadFile(files[0])}
            accept=".pdf,.png,.jpg,.jpeg"
          />
        </div>
        <div className="flex gap-12" style={{ justifyContent: 'flex-end', marginTop: 24 }}>
          <button className="btn btn-secondary" onClick={() => setShowUpload(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
            {uploading ? <><div className="spinner spinner-sm" /> Uploading...</> : <><Plus size={16} /> Upload</>}
          </button>
        </div>
      </Modal>
    </div>
  )
}
