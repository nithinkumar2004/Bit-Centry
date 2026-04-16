import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Download, FileJson, Play,
  CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronUp
} from 'lucide-react'
import {
  fetchEvaluations, fetchTenders, runEvaluation,
  exportEvaluationCSV, exportEvaluationJSON
} from '../api/client'
import StatusBadge from '../components/StatusBadge'

export default function Evaluations({ addToast }) {
  const { tenderId } = useParams()
  const navigate = useNavigate()
  const [tenders, setTenders] = useState([])
  const [selectedTender, setSelectedTender] = useState(tenderId || '')
  const [evaluations, setEvaluations] = useState([])
  const [tenderTitle, setTenderTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [evaluating, setEvaluating] = useState(false)
  const [expandedBidder, setExpandedBidder] = useState(null)

  useEffect(() => {
    loadTenders()
  }, [])

  useEffect(() => {
    if (selectedTender) loadEvaluations()
  }, [selectedTender])

  const loadTenders = async () => {
    try {
      const data = await fetchTenders()
      setTenders(data.tenders || [])
      if (tenderId) {
        setSelectedTender(tenderId)
      }
    } catch (err) {
      addToast('Failed to load tenders', 'error')
    } finally {
      if (!tenderId) setLoading(false)
    }
  }

  const loadEvaluations = async () => {
    setLoading(true)
    try {
      const data = await fetchEvaluations(selectedTender)
      setEvaluations(data.evaluations || [])
      setTenderTitle(data.tender_title || '')
    } catch (err) {
      setEvaluations([])
    } finally {
      setLoading(false)
    }
  }

  const handleRunEval = async () => {
    if (!selectedTender) {
      addToast('Select a tender first', 'error')
      return
    }
    setEvaluating(true)
    try {
      const result = await runEvaluation(selectedTender)
      addToast(`Evaluated ${result.evaluated_count} bidder(s)!`, 'success')
      loadEvaluations()
    } catch (err) {
      addToast('Evaluation failed: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setEvaluating(false)
    }
  }

  const statusIcon = (status) => {
    switch (status) {
      case 'Eligible': return <CheckCircle2 size={18} style={{ color: 'var(--status-eligible)' }} />
      case 'Not Eligible': return <XCircle size={18} style={{ color: 'var(--status-not-eligible)' }} />
      case 'Needs Manual Review': return <AlertTriangle size={18} style={{ color: 'var(--status-review)' }} />
      default: return null
    }
  }

  const decisionClass = (d) => {
    if (d === 'Eligible') return 'eligible'
    if (d === 'Not Eligible') return 'not-eligible'
    return 'review'
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Evaluations</h1>
        <p className="page-subtitle">View and manage bid evaluation results</p>
      </div>

      {/* Tender Selector */}
      <div className="card mb-24">
        <div className="flex items-center gap-16 flex-wrap">
          <div style={{ flex: 1, minWidth: 250 }}>
            <label className="form-label">Select Tender</label>
            <select
              className="form-input"
              value={selectedTender}
              onChange={e => setSelectedTender(e.target.value)}
            >
              <option value="">— Select a tender —</option>
              {tenders.map(t => (
                <option key={t.id} value={t.id}>{t.title} ({t.criteria_count} criteria)</option>
              ))}
            </select>
          </div>
          <div className="flex gap-12" style={{ paddingTop: 24 }}>
            <button
              className="btn btn-success"
              onClick={handleRunEval}
              disabled={!selectedTender || evaluating}
            >
              {evaluating
                ? <><div className="spinner spinner-sm" /> Running...</>
                : <><Play size={16} /> Run Evaluation</>
              }
            </button>
            {evaluations.length > 0 && (
              <>
                <button
                  className="btn btn-secondary"
                  onClick={() => exportEvaluationCSV(selectedTender).then(() => addToast('CSV exported!', 'success'))}
                >
                  <Download size={16} /> CSV
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => exportEvaluationJSON(selectedTender).then(() => addToast('JSON exported!', 'success'))}
                >
                  <FileJson size={16} /> JSON
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
          <div className="loading-text">Loading evaluations...</div>
        </div>
      ) : !selectedTender ? (
        <div className="card empty-state">
          <div className="empty-state-title">Select a tender to view evaluations</div>
        </div>
      ) : evaluations.length === 0 ? (
        <div className="card empty-state">
          <CheckCircle2 className="empty-state-icon" size={64} />
          <div className="empty-state-title">No evaluations yet</div>
          <div className="empty-state-text">Run an evaluation to see results</div>
        </div>
      ) : (
        <div className="flex flex-col gap-20">
          {/* Summary Row */}
          <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <div className="card stat-card green">
              <div className="stat-card-header">
                <span className="stat-card-label">Eligible</span>
                <div className="stat-card-icon"><CheckCircle2 size={22} /></div>
              </div>
              <div className="stat-card-value">
                {evaluations.filter(e => e.final_status === 'Eligible').length}
              </div>
            </div>
            <div className="card stat-card rose">
              <div className="stat-card-header">
                <span className="stat-card-label">Not Eligible</span>
                <div className="stat-card-icon"><XCircle size={22} /></div>
              </div>
              <div className="stat-card-value">
                {evaluations.filter(e => e.final_status === 'Not Eligible').length}
              </div>
            </div>
            <div className="card stat-card amber">
              <div className="stat-card-header">
                <span className="stat-card-label">Needs Review</span>
                <div className="stat-card-icon"><AlertTriangle size={22} /></div>
              </div>
              <div className="stat-card-value">
                {evaluations.filter(e => e.final_status === 'Needs Manual Review').length}
              </div>
            </div>
          </div>

          {/* Bidder Results */}
          {evaluations.map(ev => (
            <div key={ev.id} className={`card eval-result-card ${decisionClass(ev.final_status)}`}>
              <div
                className="flex items-center justify-between"
                style={{ cursor: 'pointer' }}
                onClick={() => setExpandedBidder(expandedBidder === ev.id ? null : ev.id)}
              >
                <div className="flex items-center gap-16">
                  {statusIcon(ev.final_status)}
                  <div>
                    <div className="font-bold" style={{ fontSize: 16 }}>{ev.bidder_name}</div>
                    <div className="text-sm text-muted mt-4">
                      Confidence: {(ev.overall_confidence * 100).toFixed(0)}% •{' '}
                      {ev.ambiguous_count > 0 && `${ev.ambiguous_count} ambiguous •`}{' '}
                      {ev.results?.length || 0} criteria evaluated
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-12">
                  <StatusBadge status={ev.final_status} />
                  {expandedBidder === ev.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </div>
              </div>

              {/* Expanded Details */}
              {expandedBidder === ev.id && ev.results && (
                <div className="mt-24">
                  <div className="table-container" style={{ borderRadius: 10 }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Criterion</th>
                          <th>Type</th>
                          <th>Extracted Value</th>
                          <th>Threshold</th>
                          <th>Decision</th>
                          <th>Confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ev.results.map((r, i) => (
                          <tr key={i}>
                            <td className="text-muted">{r.criterion_id}</td>
                            <td style={{ maxWidth: 250 }}>{r.criterion_description}</td>
                            <td>
                              <span className={`criterion-type ${r.criterion_type}`}>
                                {r.criterion_type}
                              </span>
                            </td>
                            <td className="font-semibold">{r.extracted_value || '—'}</td>
                            <td className="text-muted">{r.threshold || '—'}</td>
                            <td><StatusBadge status={r.decision} /></td>
                            <td>{(r.confidence * 100).toFixed(0)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Explanations */}
                  <div className="mt-16">
                    <div className="font-semibold mb-12 text-sm" style={{ textTransform: 'uppercase', letterSpacing: 0.5, color: 'var(--text-muted)' }}>
                      Explanations
                    </div>
                    {ev.results.map((r, i) => (
                      <div key={i} className="eval-explanation mb-8">
                        <strong>{r.criterion_id}:</strong> {r.explanation || 'No explanation available.'}
                        {r.source_document && (
                          <span className="text-muted text-sm"> — Source: {r.source_document}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
