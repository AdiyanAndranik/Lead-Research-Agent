import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  getPipelineStatus, getPipelineLeads,
  getPipelineScores, getPipelineEmails,
} from '../api/client'
import { StatusBadge, ScoreBar, Card, Badge, Skeleton } from '../components/ui'
import { RefreshCw, ArrowLeft, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react'
import LeadTable from '../components/LeadTable'
import Analytics from '../components/Analytics'


// ── Main page ──────────────────────────────────────────────────────────────
export default function RunDetail() {
  const { runId } = useParams()
  const [status, setStatus] = useState(null)
  const [leads, setLeads] = useState([])
  const [scores, setScores] = useState([])
  const [emails, setEmails] = useState([])
  const [tab, setTab] = useState('leads')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const refresh = useCallback(async (silent = false) => {
    if (!silent) setRefreshing(true)
    try {
      const [s, l, sc, em] = await Promise.allSettled([
        getPipelineStatus(runId),
        getPipelineLeads(runId),
        getPipelineScores(runId),
        getPipelineEmails(runId),
      ])
      if (s.status === 'fulfilled') setStatus(s.value.data)
      if (l.status === 'fulfilled') setLeads(l.value.data.leads || [])
      if (sc.status === 'fulfilled') setScores(sc.value.data.scores || [])
      if (em.status === 'fulfilled') setEmails(em.value.data.emails || [])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [runId])

  useEffect(() => {
    // Initial load
    refresh(true)

    // WebSocket for real-time updates
    const ws = new WebSocket(`ws://localhost:8000/ws/pipeline/${runId}`)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setStatus(prev => prev ? {
        ...prev,
        status: data.run_status,
        total_leads: data.total_leads,
        processed_leads: data.processed_leads,
      } : null)
      setLeads(data.leads || [])
    }

    ws.onerror = () => {
      // Fall back to polling if WebSocket fails
      const iv = setInterval(() => refresh(true), 8000)
      return () => clearInterval(iv)
    }

    return () => ws.close()
  }, [refresh, runId])

  const isRunning = status?.status === 'running' || status?.status === 'pending'
  const processed = leads.filter(l =>
    !['queued', 'researching', 'scoring', 'generating_email'].includes(l.status)
  ).length
  const pct = status?.total_leads ? Math.round((processed / status.total_leads) * 100) : 0

  return (
    <div style={{ padding: '40px 48px', maxWidth: 860, margin: '0 auto' }}>
      {/* Header */}
      <div className="fade-up" style={{ marginBottom: 28 }}>
        <Link
          to="/"
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--t3)', fontSize: 13, textDecoration: 'none', marginBottom: 16 }}
        >
          <ArrowLeft size={13} /> All runs
        </Link>

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--t1)', margin: 0 }}>
                Pipeline run
              </h1>
              {status && <StatusBadge status={status.status} />}
            </div>
            <div style={{ fontSize: 12, fontFamily: 'JetBrains Mono, monospace', color: 'var(--t3)' }}>
              {runId}
            </div>
          </div>
          <button
            onClick={() => refresh(false)}
            disabled={refreshing}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 7, padding: '7px 12px',
              fontSize: 12, color: 'var(--t2)',
              cursor: 'pointer', fontFamily: 'Inter, sans-serif',
              opacity: refreshing ? 0.5 : 1,
            }}
          >
            <RefreshCw size={12} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      {/* Progress card */}
      <Card className="fade-up-1" style={{ marginBottom: 20, padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <div style={{ fontSize: 13, color: 'var(--t2)' }}>
            {loading ? (
              <Skeleton width={120} height={14} />
            ) : (
              <span>
                <span style={{ color: 'var(--t1)', fontWeight: 500 }}>{processed}</span>
                {' of '}
                <span style={{ color: 'var(--t1)', fontWeight: 500 }}>{status?.total_leads || 0}</span>
                {' leads processed'}
              </span>
            )}
          </div>
          <span style={{ fontSize: 12, fontFamily: 'JetBrains Mono, monospace', color: 'var(--t3)' }}>
            {pct}%
          </span>
        </div>
        <div style={{ height: 3, background: 'var(--s2)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: `${pct}%`,
            background: pct === 100 ? 'var(--green)' : 'var(--accent)',
            borderRadius: 2,
            transition: 'width 0.6s ease',
          }} />
        </div>
        {isRunning && (
          <div style={{ fontSize: 11, color: 'var(--t3)', marginTop: 8 }}>
            Auto-refreshing every 8s…
          </div>
        )}
      </Card>

      {/* Tabs */}
      <div className="fade-up-2" style={{
        display: 'flex', gap: 2, marginBottom: 20,
        background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: 8, padding: 4,
      }}>
        {[
          { id: 'leads', label: 'Leads', count: leads.length },
          { id: 'scores', label: 'Scores', count: scores.length },
          { id: 'emails', label: 'Emails', count: emails.length },
          { id: 'table', label: 'Table', count: leads.length },
          { id: 'analytics', label: 'Analytics' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              padding: '7px 12px',
              background: tab === t.id ? 'var(--s2)' : 'transparent',
              border: tab === t.id ? '1px solid var(--border)' : '1px solid transparent',
              borderRadius: 6, fontSize: 13, fontWeight: 500,
              color: tab === t.id ? 'var(--t1)' : 'var(--t2)',
              cursor: 'pointer', fontFamily: 'Inter, sans-serif',
              transition: 'all 0.15s',
            }}
          >
            {t.label}
            {t.count !== undefined && t.count > 0 && (
              <span style={{
                background: tab === t.id ? 'var(--accent-dim)' : 'var(--border)',
                color: tab === t.id ? 'var(--accent)' : 'var(--t3)',
                fontSize: 11, fontWeight: 600, fontFamily: 'JetBrains Mono, monospace',
                padding: '1px 6px', borderRadius: 10,
              }}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {loading ? (
        <LoadingSkeleton />
        ) : (
        <>
            {tab === 'leads' && <LeadsTab leads={leads} />}

            {tab === 'scores' && <ScoresTab scores={scores} />}

            {tab === 'emails' && (
            <div>
                {emails.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                    <Link
                    to={`/runs/${runId}/review`}
                    style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        background: 'var(--accent)',
                        color: 'white',
                        padding: '8px 16px',
                        borderRadius: 8,
                        fontSize: 13,
                        fontWeight: 500,
                        textDecoration: 'none',
                    }}
                    >
                    Open review queue →
                    </Link>
                </div>
                )}

                <EmailsTab emails={emails} runId={runId} />
            </div>
            )}
            {tab === 'table' && (
                <LeadTable
                    leads={leads}
                    scores={scores}
                />
            )}
            {tab === 'analytics' && (
                <Analytics
                    leads={leads}
                    scores={scores}
                    emails={emails}
                />
            )}
        </>
        )}
    </div>
  )
}

// ── Leads tab ──────────────────────────────────────────────────────────────
function LeadsTab({ leads }) {
  if (leads.length === 0) return <EmptyTab message="No leads found for this run." />

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {leads.map((lead, i) => (
        <div
          key={lead.id}
          className={`fade-up-${Math.min(i + 1, 5)}`}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 8, padding: '12px 16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <CompanyAvatar name={lead.company_name} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--t1)' }}>
                {lead.company_name}
              </div>
              <div style={{ fontSize: 12, color: 'var(--t3)', fontFamily: 'JetBrains Mono, monospace', marginTop: 2 }}>
                {lead.domain || '—'}
              </div>
            </div>
          </div>
          <StatusBadge status={lead.status} />
        </div>
      ))}
    </div>
  )
}

// ── Scores tab — the signature piece ──────────────────────────────────────
function ScoresTab({ scores }) {
  if (scores.length === 0) return (
    <EmptyTab message="Scores appear here as leads finish research. Check back in a moment." />
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {scores.map((score, i) => (
        <ScoreCard key={i} score={score} index={i} />
      ))}
    </div>
  )
}

function ScoreCard({ score, index }) {
  const [open, setOpen] = useState(false)
  const dims = score.dimensions || {}
  const dimReasons = score.dimension_reasoning || {}
  const passed = score.passed_threshold
  const actionColor = score.recommended_action === 'prioritize'
    ? 'green' : score.recommended_action === 'nurture' ? 'amber' : 'gray'

  return (
    <Card className={`fade-up-${Math.min(index + 1, 5)}`} style={{ overflow: 'hidden' }}>
      {/* Header row */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 18px',
          background: 'transparent', border: 'none',
          cursor: 'pointer', textAlign: 'left',
          transition: 'background 0.15s',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--s2)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <CompanyAvatar name={score.company_name} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--t1)', marginBottom: 4 }}>
              {score.company_name}
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <Badge label={score.recommended_action} variant={actionColor} />
              {!passed && <Badge label="Below threshold" variant="gray" />}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {/* Big score number */}
          <div style={{ textAlign: 'right' }}>
            <div style={{
              fontSize: 28, fontWeight: 700,
              fontFamily: 'JetBrains Mono, monospace',
              color: score.overall_score >= 7 ? 'var(--green)'
                : score.overall_score >= 5 ? 'var(--amber)' : 'var(--red)',
              lineHeight: 1,
            }}>
              {score.overall_score}
              <span style={{ fontSize: 14, color: 'var(--t3)', fontWeight: 400 }}>/10</span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--t3)', marginTop: 3 }}>
              {Math.round(score.confidence * 100)}% confidence
            </div>
          </div>
          {open ? <ChevronUp size={14} color="var(--t3)" /> : <ChevronDown size={14} color="var(--t3)" />}
        </div>
      </button>

      {/* Expanded detail */}
      {open && (
        <div style={{ borderTop: '1px solid var(--border)', padding: '16px 18px' }}>
          {/* Reasoning */}
          <p style={{ fontSize: 13, color: 'var(--t2)', lineHeight: 1.6, marginBottom: 18 }}>
            {score.reasoning}
          </p>

          {/* Dimension scores — the signature element */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {Object.entries(dims).map(([key, val], i) => (
              <div key={key} className={`fade-up-${i + 1}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--t2)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {key.replace(/_/g, ' ')}
                  </span>
                </div>
                <ScoreBar score={val} animate />
                {dimReasons[key] && (
                  <p style={{ fontSize: 11, color: 'var(--t3)', margin: '5px 0 0', lineHeight: 1.5 }}>
                    {dimReasons[key]}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

// ── Emails tab ─────────────────────────────────────────────────────────────
function EmailsTab({ emails, runId }) {
  if (emails.length === 0) return (
    <EmptyTab message="Emails appear here after scoring completes for qualifying leads." />
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {emails.map((email, i) => (
        <EmailCard key={i} email={email} index={i} runId={runId} />
      ))}
    </div>
  )
}

function EmailCard({ email, index, runId }) {
  const [copied, setCopied] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(`Subject: ${email.subject_line}\n\n${email.body}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card className={`fade-up-${Math.min(index + 1, 5)}`}>
      {/* Company header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px', borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <CompanyAvatar name={email.company_name} size={28} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--t1)' }}>
              {email.company_name}
            </div>
            <div style={{ fontSize: 11, color: 'var(--t3)', fontFamily: 'JetBrains Mono, monospace' }}>
              {email.domain}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 11, color: 'var(--t3)' }}>{email.word_count}w</span>
          <button
            onClick={copy}
            style={{
              display: 'flex', alignItems: 'center', gap: 5,
              background: copied ? 'var(--green-dim)' : 'var(--s2)',
              border: `1px solid ${copied ? 'rgba(16,185,129,0.25)' : 'var(--border)'}`,
              borderRadius: 6, padding: '5px 10px',
              fontSize: 12, color: copied ? 'var(--green)' : 'var(--t2)',
              cursor: 'pointer', fontFamily: 'Inter, sans-serif',
              transition: 'all 0.15s',
            }}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Email content */}
      <div style={{ padding: '16px' }}>
        {/* Subject */}
        <div style={{
          fontSize: 11, fontWeight: 600, color: 'var(--t3)',
          textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6,
        }}>
          Subject
        </div>
        <div style={{
          fontSize: 13, fontWeight: 500, color: 'var(--t1)',
          marginBottom: 16, paddingBottom: 14,
          borderBottom: '1px solid var(--border-light)',
        }}>
          {email.subject_line}
        </div>

        {/* Body */}
        <div style={{
          fontSize: 13, color: 'var(--t2)',
          lineHeight: 1.7, whiteSpace: 'pre-wrap',
        }}>
          {email.body}
        </div>

        {/* Quality flags */}
        {email.quality_flags?.length > 0 && (
          <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {email.quality_flags.map((f, i) => (
              <span key={i} style={{
                fontSize: 11, color: 'var(--amber)',
                background: 'var(--amber-dim)',
                border: '1px solid rgba(245,158,11,0.2)',
                borderRadius: 4, padding: '2px 8px',
              }}>
                {f}
              </span>
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}

// ── Shared helpers ─────────────────────────────────────────────────────────
function CompanyAvatar({ name, size = 32 }) {
  const initials = name
    .split(' ')
    .slice(0, 2)
    .map(w => w[0])
    .join('')
    .toUpperCase()

  const hue = name.charCodeAt(0) * 15 % 360

  return (
    <div style={{
      width: size, height: size, borderRadius: 8,
      background: `hsl(${hue}, 60%, 20%)`,
      border: `1px solid hsl(${hue}, 60%, 30%)`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.35, fontWeight: 600,
      color: `hsl(${hue}, 80%, 75%)`,
      flexShrink: 0,
      fontFamily: 'Inter, sans-serif',
    }}>
      {initials}
    </div>
  )
}

function EmptyTab({ message }) {
  return (
    <div style={{
      padding: '60px 20px', textAlign: 'center',
      color: 'var(--t3)', fontSize: 13,
      border: '1px dashed var(--border)', borderRadius: 10,
    }}>
      {message}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {[1, 2, 3].map(i => (
        <div key={i} style={{
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 10, padding: '14px 18px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <Skeleton width={32} height={32} style={{ borderRadius: 8 }} />
            <div>
              <Skeleton width={120} height={13} style={{ marginBottom: 6 }} />
              <Skeleton width={80} height={11} />
            </div>
          </div>
          <Skeleton width={70} height={22} style={{ borderRadius: 20 }} />
        </div>
      ))}
    </div>
  )
}