import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Sparkles, Users, Play, FileText,
  DollarSign, Award, Briefcase, AlertCircle
} from 'lucide-react'
import { fetchTender, extractCriteria, fetchBidders, runEvaluation } from '../api/client'
import StatusBadge from '../components/StatusBadge'

export default function TenderDetail({ addToast }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tender, setTender] = useState(null)
  const [bidders, setBidders] = useState([])
  const [loading, setLoading] = useState(true)
  const [extracting, setExtracting] = useState(false)
  const [evaluating, setEvaluating] = useState(false)

  useEffect(() => {
    loadData()
  }, [id])

  const loadData = async () => {
    try {
      const [tenderData, bidderData] = await Promise.all([
        fetchTender(id),
        fetchBidders(id)
      ])
      setTender(tenderData)
      setBidders(bidderData.bidders || [])
    } catch (err) {
      addToast('Failed to load tender details', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleExtract = async () => {
    setExtracting(true)
    try {
      const result = await extractCriteria(id)
      addToast(`Extracted ${result.count} criteria!`, 'success')
      loadData()
    } catch (err) {
      addToast('Extraction failed', 'error')
    } finally {
      setExtracting(false)
    }
  }

  const handleEvaluate = async () => {
    if (bidders.length === 0) {
      addToast('No bidders to evaluate. Upload bidder documents first.', 'error')
      return
    }
    setEvaluating(true)
    try {
      const result = await runEvaluation(id)
      addToast(`Evaluated ${result.evaluated_count} bidder(s)!`, 'success')
      navigate(`/evaluations/${id}`)
    } catch (err) {
      addToast('Evaluation failed: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setEvaluating(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <div className="loading-text">Loading tender...</div>
      </div>
    )
  }

  if (!tender) {
    return (
      <div className="empty-state">
        <div className="empty-state-title">Tender not found</div>
        <button className="btn btn-secondary mt-16" onClick={() => navigate('/tenders')}>
          <ArrowLeft size={16} /> Back to Tenders
        </button>
      </div>
    )
  }

  const typeIcon = (type) => {
    switch (type) {
      case 'financial': return <DollarSign size={16} />
      case 'technical': return <Briefcase size={16} />
      case 'compliance': return <Award size={16} />
      default: return <FileText size={16} />
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <button className="btn btn-secondary btn-sm mb-16" onClick={() => navigate('/tenders')}>
          <ArrowLeft size={14} /> Back
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">{tender.title}</h1>
            <div className="flex items-center gap-12 mt-8">
              <StatusBadge status={tender.status} />
              <span className="text-sm text-muted">
                {tender.original_filename}
              </span>
              <span className="text-sm text-muted">
                OCR: {(tender.ocr_confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="flex gap-12">
            {tender.status === 'uploaded' && (
              <button className="btn btn-primary" onClick={handleExtract} disabled={extracting}>
                {extracting
                  ? <><div className="spinner spinner-sm" /> Extracting...</>
                  : <><Sparkles size={18} /> Extract Criteria</>
                }
              </button>
            )}
            {tender.status === 'ready' && (
              <button className="btn btn-success" onClick={handleEvaluate} disabled={evaluating}>
                {evaluating
                  ? <><div className="spinner spinner-sm" /> Evaluating...</>
                  : <><Play size={18} /> Run Evaluation</>
                }
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Criteria */}
      <div className="mb-24">
        <h2 className="font-semibold mb-16" style={{ fontSize: 18 }}>
          Eligibility Criteria ({tender.criteria?.length || 0})
        </h2>
        {tender.criteria && tender.criteria.length > 0 ? (
          <div className="criteria-grid">
            {tender.criteria.map((c, i) => (
              <div key={i} className="card criterion-card">
                <div className="flex items-center gap-8 mb-8">
                  <span style={{ color: c.type === 'financial' ? 'var(--accent-blue)' : c.type === 'technical' ? 'var(--accent-purple)' : 'var(--status-review)' }}>
                    {typeIcon(c.type)}
                  </span>
                  <span className={`criterion-type ${c.type}`}>{c.type}</span>
                  {c.mandatory && <span className="badge badge-not-eligible" style={{ fontSize: 10, padding: '2px 8px' }}>Mandatory</span>}
                </div>
                <div className="criterion-desc">{c.description}</div>
                <div className="criterion-meta">
                  <span>ID: {c.id}</span>
                  {c.threshold && <span>Threshold: {c.threshold} {c.unit || ''}</span>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card" style={{ textAlign: 'center', padding: 32 }}>
            <AlertCircle size={32} style={{ color: 'var(--text-muted)', margin: '0 auto 12px' }} />
            <div className="text-secondary">No criteria extracted yet.</div>
            {tender.status === 'uploaded' && (
              <button className="btn btn-primary btn-sm mt-16" onClick={handleExtract}>
                <Sparkles size={14} /> Extract Now
              </button>
            )}
          </div>
        )}
      </div>

      {/* Associated Bidders */}
      <div>
        <div className="flex items-center justify-between mb-16">
          <h2 className="font-semibold" style={{ fontSize: 18 }}>
            Associated Bidders ({bidders.length})
          </h2>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/bidders')}>
            <Users size={14} /> Manage Bidders
          </button>
        </div>
        {bidders.length > 0 ? (
          <div className="table-container card" style={{ padding: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Documents</th>
                  <th>Turnover</th>
                  <th>Certifications</th>
                  <th>Projects</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {bidders.map(b => (
                  <tr key={b.id}>
                    <td className="font-semibold">{b.name}</td>
                    <td>{b.documents_count} files</td>
                    <td>{b.turnover ? `₹${b.turnover} Cr` : '—'}</td>
                    <td>
                      <div className="flex flex-wrap gap-4">
                        {b.certifications?.map((c, i) => (
                          <span key={i} className="badge badge-info" style={{ fontSize: 11 }}>{c}</span>
                        ))}
                        {(!b.certifications || b.certifications.length === 0) && '—'}
                      </div>
                    </td>
                    <td>{b.project_count ?? '—'}</td>
                    <td>{(b.confidence * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card text-center" style={{ padding: 32 }}>
            <div className="text-muted">No bidders linked to this tender yet.</div>
          </div>
        )}
      </div>

      {/* Raw Text Preview */}
      {tender.raw_text && (
        <div className="mt-24">
          <h2 className="font-semibold mb-16" style={{ fontSize: 18 }}>Extracted Text Preview</h2>
          <div className="card" style={{ maxHeight: 300, overflow: 'auto', fontFamily: 'monospace', fontSize: 13, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
            {tender.raw_text.slice(0, 3000)}
            {tender.raw_text.length > 3000 && '\n\n... (truncated)'}
          </div>
        </div>
      )}
    </div>
  )
}
