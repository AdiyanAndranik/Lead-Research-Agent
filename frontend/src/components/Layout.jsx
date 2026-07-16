import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Plus, Zap } from 'lucide-react'

export default function Layout({ children }) {
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Sidebar */}
      <aside style={{
        width: 220,
        minHeight: '100vh',
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
      }}>
        {/* Logo */}
        <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 28, height: 28,
              background: 'var(--accent)',
              borderRadius: 8,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Zap size={14} color="white" fill="white" />
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text)', lineHeight: 1.2 }}>
                Lead Agent
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 1 }}>
                Research · Score · Reach
              </div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ padding: '12px 10px', flex: 1 }}>
          <NavItem to="/" icon={<LayoutDashboard size={15} />} label="Runs" />
        </nav>

        {/* New run button */}
        <div style={{ padding: '12px 10px', borderTop: '1px solid var(--border)' }}>
          <button
            onClick={() => navigate('/new')}
            style={{
              width: '100%',
              display: 'flex', alignItems: 'center', gap: 8,
              background: 'var(--accent)',
              color: 'white',
              border: 'none',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              fontFamily: 'Inter, sans-serif',
            }}
          >
            <Plus size={14} />
            New run
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ marginLeft: 220, flex: 1, minHeight: '100vh' }}>
        {children}
      </main>
    </div>
  )
}

function NavItem({ to, icon, label }) {
  return (
    <NavLink
      to={to}
      end
      style={({ isActive }) => ({
        display: 'flex',
        alignItems: 'center',
        gap: 9,
        padding: '7px 10px',
        borderRadius: 7,
        fontSize: 13,
        fontWeight: 500,
        color: isActive ? 'var(--text)' : 'var(--text-2)',
        background: isActive ? 'var(--s2)' : 'transparent',
        textDecoration: 'none',
        transition: 'all 0.15s',
      })}
    >
      {icon}
      {label}
    </NavLink>
  )
}