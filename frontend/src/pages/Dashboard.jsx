import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText,
  Users,
  CheckCircle2,
  Shield,
  TrendingUp,
  AlertTriangle,
  Upload,
  ArrowRight,
  Activity
} from 'lucide-react'
import { fetchDashboardStats } from '../api/client'

export default function Dashboard({ addToast }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await fetchDashboardStats()
      setStats(data)
    } catch (err) {
      addToast('Failed to load dashboard stats', 'error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <div className="loading-text">Loading dashboard...</div>
      </div>
    )
  }

  const s = stats || {}

  const getActionIcon = (action) => {
    const map = {
      'UPLOAD': 'upload',
      'EXTRACT': 'extract',
      'EVALUATE': 'evaluate',
      'DELETE': 'delete',
      'EXPORT': 'export',
      'PARSE': 'upload',
    }
    return map[action] || 'upload'
  }

  const formatTime = (ts) => {
    if (!ts) return ''
    try {
      const d = new Date(ts)
      const now = new Date()
      const diff = (now - d) / 1000
      if (diff < 60) return 'Just now'
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
      return d.toLocaleDateString()
    } catch {
      return ''
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">AI-Powered Tender Evaluation Overview</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="card stat-card blue" onClick={() => navigate('/tenders')} style={{ cursor: 'pointer' }}>
          <div className="stat-card-header">
            <span className="stat-card-label">Tenders</span>
            <div className="stat-card-icon"><FileText size={22} /></div>
          </div>
          <div className="stat-card-value">{s.tender_count || 0}</div>
        </div>

        <div className="card stat-card purple" onClick={() => navigate('/bidders')} style={{ cursor: 'pointer' }}>
          <div className="stat-card-header">
            <span className="stat-card-label">Bidders</span>
            <div className="stat-card-icon"><Users size={22} /></div>
          </div>
          <div className="stat-card-value">{s.bidder_count || 0}</div>
        </div>

        <div className="card stat-card green">
          <div className="stat-card-header">
            <span className="stat-card-label">Eligible</span>
            <div className="stat-card-icon"><CheckCircle2 size={22} /></div>
          </div>
          <div className="stat-card-value">{s.eligible_count || 0}</div>
        </div>

        <div className="card stat-card amber">
          <div className="stat-card-header">
            <span className="stat-card-label">Needs Review</span>
            <div className="stat-card-icon"><AlertTriangle size={22} /></div>
          </div>
          <div className="stat-card-value">{s.review_count || 0}</div>
        </div>

        <div className="card stat-card rose">
          <div className="stat-card-header">
            <span className="stat-card-label">Not Eligible</span>
            <div className="stat-card-icon"><TrendingUp size={22} /></div>
          </div>
          <div className="stat-card-value">{s.not_eligible_count || 0}</div>
        </div>
      </div>

      {/* Quick Actions + Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Quick Actions */}
        <div className="card">
          <h3 className="font-semibold mb-16" style={{ fontSize: 16 }}>Quick Actions</h3>
          <div className="flex flex-col gap-12">
            <button
              className="btn btn-primary w-full"
              onClick={() => navigate('/tenders')}
              style={{ justifyContent: 'space-between' }}
            >
              <span className="flex items-center gap-8"><Upload size={18} /> Upload Tender</span>
              <ArrowRight size={16} />
            </button>
            <button
              className="btn btn-secondary w-full"
              onClick={() => navigate('/bidders')}
              style={{ justifyContent: 'space-between' }}
            >
              <span className="flex items-center gap-8"><Users size={18} /> Add Bidder</span>
              <ArrowRight size={16} />
            </button>
            <button
              className="btn btn-secondary w-full"
              onClick={() => navigate('/evaluations')}
              style={{ justifyContent: 'space-between' }}
            >
              <span className="flex items-center gap-8"><CheckCircle2 size={18} /> View Evaluations</span>
              <ArrowRight size={16} />
            </button>
            <button
              className="btn btn-secondary w-full"
              onClick={() => navigate('/audit')}
              style={{ justifyContent: 'space-between' }}
            >
              <span className="flex items-center gap-8"><Shield size={18} /> Audit Trail</span>
              <ArrowRight size={16} />
            </button>
          </div>

          {/* Pass Rate */}
          {s.evaluation_count > 0 && (
            <div className="mt-24" style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.06)', borderRadius: 12, border: '1px solid rgba(16, 185, 129, 0.15)' }}>
              <div className="flex items-center justify-between mb-8">
                <span className="text-sm text-secondary">Pass Rate</span>
                <span className="font-bold" style={{ color: 'var(--status-eligible)', fontSize: 20 }}>
                  {s.pass_rate}%
                </span>
              </div>
              <div className="confidence-bar">
                <div
                  className={`confidence-bar-fill ${s.pass_rate >= 70 ? 'high' : s.pass_rate >= 40 ? 'medium' : 'low'}`}
                  style={{ width: `${s.pass_rate}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="flex items-center justify-between mb-16">
            <h3 className="font-semibold" style={{ fontSize: 16 }}>
              <Activity size={16} style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
              Recent Activity
            </h3>
            <button className="btn btn-sm btn-secondary" onClick={() => navigate('/audit')}>
              View All
            </button>
          </div>
          
          {s.recent_activity && s.recent_activity.length > 0 ? (
            <div className="activity-feed">
              {s.recent_activity.map((item, i) => (
                <div key={i} className="activity-item">
                  <div className={`activity-icon ${getActionIcon(item.action)}`}>
                    {item.action === 'UPLOAD' && <Upload size={16} />}
                    {item.action === 'EXTRACT' && <FileText size={16} />}
                    {item.action === 'EVALUATE' && <CheckCircle2 size={16} />}
                    {item.action === 'DELETE' && <AlertTriangle size={16} />}
                    {item.action === 'EXPORT' && <TrendingUp size={16} />}
                  </div>
                  <div className="activity-content">
                    <div className="activity-text">
                      {item.action} — {item.entity_type}
                    </div>
                    <div className="activity-time">{formatTime(item.timestamp)}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state" style={{ padding: 32 }}>
              <div className="text-muted">No activity yet. Start by uploading a tender.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
