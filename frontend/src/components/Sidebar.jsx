import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  Users,
  CheckCircle2,
  Shield,
  Sparkles
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/tenders', label: 'Tenders', icon: FileText },
  { path: '/bidders', label: 'Bidders', icon: Users },
  { path: '/evaluations', label: 'Evaluations', icon: CheckCircle2 },
  { path: '/audit', label: 'Audit Log', icon: Shield },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <Sparkles size={20} />
          </div>
          <div>
            <div className="sidebar-logo-text">BidSentry</div>
            <div className="sidebar-logo-subtitle">AI Tender Evaluation</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(item => {
          const Icon = item.icon
          const isActive = item.path === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(item.path)

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`nav-link ${isActive ? 'active' : ''}`}
            >
              <Icon className="nav-icon" size={20} />
              <span>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={14} />
          <span>Anti-Corruption System</span>
        </div>
        <div style={{ marginTop: 4, opacity: 0.6 }}>v1.0.0 — Hash-Verified</div>
      </div>
    </aside>
  )
}
