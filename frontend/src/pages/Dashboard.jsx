import { Link } from 'react-router-dom'
import { ArrowRight, Inbox } from 'lucide-react'
import { StatusBadge } from '../components/ui'

export default function Dashboard() {
  const runs = (() => {
    try { return JSON.parse(localStorage.getItem('pipeline_runs') || '[]') }
    catch { return [] }
  })()

  return (
    <div style={{ padding: '40px 48px', maxWidth: 860, margin: '0 auto' }} className="fade-up">
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: 'var(--t1)', margin: 0 }}>
          Pipeline runs
        </h1>
        <p style={{ color: 'var(--t2)', margin: '4px 0 0', fontSize: 13 }}>
          Each run researches a batch of companies end to end.
        </p>
      </div>

      {runs.length === 0 ? (
        <EmptyState />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {runs.map((run, i) => (
            <RunRow key={run.id} run={run} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}

function RunRow({ run, index }) {
  return (
    <Link
      to={`/runs/${run.id}`}
      className={`fade-up-${Math.min(index + 1, 5)}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 10,
        padding: '14px 18px',
        textDecoration: 'none',
        transition: 'border-color 0.15s, background 0.15s',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = 'var(--accent)'
        e.currentTarget.style.background = 'var(--s2)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--border)'
        e.currentTarget.style.background = 'var(--surface)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div>
          <div style={{
            fontSize: 12, fontFamily: 'JetBrains Mono, monospace',
            color: 'var(--t3)', marginBottom: 3,
          }}>
            {run.id.slice(0, 8)}
          </div>
          <div style={{ fontSize: 13, color: 'var(--t2)' }}>
            {run.created_at}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 13, color: 'var(--t1)', fontWeight: 500 }}>
            {run.total} {run.total === 1 ? 'company' : 'companies'}
          </div>
          {run.status && (
            <div style={{ marginTop: 4 }}>
              <StatusBadge status={run.status} />
            </div>
          )}
        </div>
        <ArrowRight size={14} color="var(--t3)" />
      </div>
    </Link>
  )
}

function EmptyState() {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center',
      padding: '80px 20px',
      border: '1px dashed var(--border)',
      borderRadius: 12,
      color: 'var(--t3)',
      textAlign: 'center',
    }}>
      <Inbox size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
      <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--t2)', marginBottom: 6 }}>
        No runs yet
      </div>
      <div style={{ fontSize: 13, marginBottom: 20 }}>
        Submit a list of companies to start researching.
      </div>
      <Link
        to="/new"
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          background: 'var(--accent)', color: 'white',
          padding: '8px 16px', borderRadius: 8,
          fontSize: 13, fontWeight: 500,
          textDecoration: 'none',
        }}
      >
        Start first run
      </Link>
    </div>
  )
}