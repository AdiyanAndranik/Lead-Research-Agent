import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getPipelineEmails, getPipelineScores, getLeadEmails, updateEmail } from '../api/client'
import { Badge, Card, ScoreBar, StatusBadge } from '../components/ui'
import {
  ArrowLeft, Check, X, RotateCcw, ChevronLeft,
  ChevronRight, Edit3, Save, AlertCircle
} from 'lucide-react'

export default function EmailReview() {
  const { runId } = useParams()
  const [emails, setEmails] = useState([])
  const [scores, setScores] = useState([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [variants, setVariants] = useState([])
  const [activeVariant, setActiveVariant] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editSubject, setEditSubject] = useState('')
  const [editBody, setEditBody] = useState('')
  const [toast, setToast] = useState(null)
  const bodyRef = useRef(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [em, sc] = await Promise.all([
          getPipelineEmails(runId),
          getPipelineScores(runId),
        ])
        setEmails(em.data.emails || [])
        setScores(sc.data.scores || [])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [runId])

  const currentEmail = emails[selectedIndex]
  const currentScore = scores.find(s => s.company_name === currentEmail?.company_name)

  useEffect(() => {
    if (!currentEmail) return
    const load = async () => {
      try {
        const res = await getLeadEmails(runId, currentEmail.lead_id || '')
        setVariants(res.data.variants || [])
        setActiveVariant(0)
      } catch {
        setVariants([])
      }
    }
    // We need lead_id — let's use what the emails endpoint gives us
    // If no lead_id in email object, skip
    if (currentEmail.lead_id) load()
  }, [currentEmail, runId])

  const activeEmail = variants[activeVariant] || currentEmail

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const startEdit = () => {
    setEditSubject(activeEmail.subject_line)
    setEditBody(activeEmail.body)
    setEditing(true)
    setTimeout(() => bodyRef.current?.focus(), 50)
  }

  const cancelEdit = () => {
    setEditing(false)
  }

  const saveEdit = async () => {
    if (!activeEmail.id) return
    setSaving(true)
    try {
      await updateEmail(runId, currentEmail.lead_id, activeEmail.id, {
        subject_line: editSubject,
        body: editBody,
      })
      // Update local state
      const updated = [...variants]
      updated[activeVariant] = { ...updated[activeVariant], subject_line: editSubject, body: editBody }
      setVariants(updated)
      setEditing(false)
      showToast('Changes saved')
    } catch {
      showToast('Save failed', 'error')
    } finally {
      setSaving(false)
    }
  }

  const updateStatus = async (status) => {
    if (!activeEmail.id) return
    setSaving(true)
    try {
      await updateEmail(runId, currentEmail.lead_id, activeEmail.id, { status })
      const updated = [...variants]
      updated[activeVariant] = { ...updated[activeVariant], status }
      setVariants(updated)
      const emailsCopy = [...emails]
      emailsCopy[selectedIndex] = { ...emailsCopy[selectedIndex], status }
      setEmails(emailsCopy)
      showToast(status === 'approved' ? 'Email approved ✓' : 'Email rejected')
    } catch {
      showToast('Action failed', 'error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return (
    <div style={{ padding: '40px 48px', color: 'var(--t3)', fontSize: 13 }}>
      Loading email review queue…
    </div>
  )

  if (emails.length === 0) return (
    <div style={{ padding: '40px 48px' }}>
      <Link to={`/runs/${runId}`} style={{ color: 'var(--t3)', fontSize: 13, textDecoration: 'none' }}>
        <ArrowLeft size={13} style={{ marginRight: 6 }} />Back
      </Link>
      <div style={{ marginTop: 40, textAlign: 'center', color: 'var(--t3)' }}>
        No emails ready for review yet.
      </div>
    </div>
  )

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top bar */}
      <div style={{
        padding: '12px 24px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Link
            to={`/runs/${runId}`}
            style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--t3)', fontSize: 13, textDecoration: 'none' }}
          >
            <ArrowLeft size={13} /> Back
          </Link>
          <div style={{ width: 1, height: 16, background: 'var(--border)' }} />
          <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--t1)' }}>
            Email Review
          </span>
          <span style={{ fontSize: 12, color: 'var(--t3)' }}>
            {selectedIndex + 1} of {emails.length}
          </span>
        </div>

        {/* Navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <NavButton
            onClick={() => { setSelectedIndex(i => Math.max(0, i - 1)); setEditing(false) }}
            disabled={selectedIndex === 0}
            icon={<ChevronLeft size={14} />}
          />
          <NavButton
            onClick={() => { setSelectedIndex(i => Math.min(emails.length - 1, i + 1)); setEditing(false) }}
            disabled={selectedIndex === emails.length - 1}
            icon={<ChevronRight size={14} />}
          />
        </div>
      </div>

      {/* Body — two columns */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* Left — company list */}
        <div style={{
          width: 240, borderRight: '1px solid var(--border)',
          background: 'var(--surface)', overflowY: 'auto', flexShrink: 0,
        }}>
          {emails.map((email, i) => (
            <button
              key={i}
              onClick={() => { setSelectedIndex(i); setEditing(false) }}
              style={{
                width: '100%', padding: '12px 16px',
                background: i === selectedIndex ? 'var(--s2)' : 'transparent',
                borderBottom: '1px solid var(--border-light)',
                border: 'none', borderBottom: '1px solid var(--border)',
                cursor: 'pointer', textAlign: 'left',
                borderLeft: i === selectedIndex ? '2px solid var(--accent)' : '2px solid transparent',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--t1)' }}>
                  {email.company_name}
                </span>
                <StatusDot status={email.status} />
              </div>
              <div style={{ fontSize: 11, color: 'var(--t3)', fontFamily: 'JetBrains Mono, monospace' }}>
                {email.domain}
              </div>
            </button>
          ))}
        </div>

        {/* Right — email editor */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
          {currentEmail && (
            <div className="fade-up">
              {/* Company header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20 }}>
                <div>
                  <h2 style={{ fontSize: 18, fontWeight: 600, color: 'var(--t1)', margin: '0 0 4px' }}>
                    {currentEmail.company_name}
                  </h2>
                  <div style={{ fontSize: 12, color: 'var(--t3)', fontFamily: 'JetBrains Mono, monospace' }}>
                    {currentEmail.domain}
                  </div>
                </div>

                {/* Score pill */}
                {currentScore && (
                  <div style={{
                    background: 'var(--s2)', border: '1px solid var(--border)',
                    borderRadius: 10, padding: '10px 16px', textAlign: 'center',
                  }}>
                    <div style={{
                      fontSize: 24, fontWeight: 700,
                      fontFamily: 'JetBrains Mono, monospace',
                      color: currentScore.overall_score >= 7 ? 'var(--green)'
                        : currentScore.overall_score >= 5 ? 'var(--amber)' : 'var(--red)',
                      lineHeight: 1,
                    }}>
                      {currentScore.overall_score}
                      <span style={{ fontSize: 12, color: 'var(--t3)', fontWeight: 400 }}>/10</span>
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--t3)', marginTop: 3 }}>
                      lead score
                    </div>
                  </div>
                )}
              </div>

              {/* Score dimensions mini */}
              {currentScore && (
                <Card style={{ padding: '12px 16px', marginBottom: 20 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 20px' }}>
                    {Object.entries(currentScore.dimensions || {}).map(([key, val]) => (
                      <div key={key}>
                        <div style={{ fontSize: 10, color: 'var(--t3)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                          {key.replace(/_/g, ' ')}
                        </div>
                        <ScoreBar score={val} animate />
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Variant switcher */}
              {variants.length > 1 && (
                <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
                  {variants.map((v, i) => (
                    <button
                      key={i}
                      onClick={() => { setActiveVariant(i); setEditing(false) }}
                      style={{
                        padding: '5px 12px',
                        background: activeVariant === i ? 'var(--accent-dim)' : 'var(--s2)',
                        border: `1px solid ${activeVariant === i ? 'rgba(99,102,241,0.3)' : 'var(--border)'}`,
                        borderRadius: 6, fontSize: 11, fontWeight: 500,
                        color: activeVariant === i ? 'var(--accent)' : 'var(--t2)',
                        cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                        transition: 'all 0.15s',
                      }}
                    >
                      {v.variant?.replace(/_/g, ' ').replace('first', '').trim()}
                      {v.status === 'approved' && <span style={{ color: 'var(--green)', marginLeft: 4 }}>✓</span>}
                    </button>
                  ))}
                </div>
              )}

              {/* Email card */}
              <Card style={{ marginBottom: 16 }}>
                {/* Subject */}
                <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 10, color: 'var(--t3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
                    Subject line
                  </div>
                  {editing ? (
                    <input
                      value={editSubject}
                      onChange={e => setEditSubject(e.target.value)}
                      style={{
                        width: '100%', background: 'var(--s2)',
                        border: '1px solid var(--accent)',
                        borderRadius: 6, padding: '8px 10px',
                        fontSize: 14, fontWeight: 500,
                        color: 'var(--t1)', fontFamily: 'Inter, sans-serif',
                        outline: 'none',
                      }}
                    />
                  ) : (
                    <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--t1)' }}>
                      {activeEmail?.subject_line || currentEmail.subject_line}
                    </div>
                  )}
                </div>

                {/* Body */}
                <div style={{ padding: '14px 18px' }}>
                  <div style={{ fontSize: 10, color: 'var(--t3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
                    Email body
                  </div>
                  {editing ? (
                    <textarea
                      ref={bodyRef}
                      value={editBody}
                      onChange={e => setEditBody(e.target.value)}
                      rows={8}
                      style={{
                        width: '100%', background: 'var(--s2)',
                        border: '1px solid var(--accent)',
                        borderRadius: 6, padding: '10px 12px',
                        fontSize: 13, color: 'var(--t1)',
                        fontFamily: 'Inter, sans-serif',
                        lineHeight: 1.7, resize: 'vertical',
                        outline: 'none',
                      }}
                    />
                  ) : (
                    <div style={{ fontSize: 13, color: 'var(--t2)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                      {activeEmail?.body || currentEmail.body}
                    </div>
                  )}
                </div>

                {/* Quality flags */}
                {(activeEmail?.quality_flags || currentEmail.quality_flags)?.length > 0 && (
                  <div style={{
                    padding: '10px 18px', borderTop: '1px solid var(--border)',
                    display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center',
                  }}>
                    <AlertCircle size={12} color="var(--amber)" />
                    {(activeEmail?.quality_flags || currentEmail.quality_flags).map((f, i) => (
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
              </Card>

              {/* Action bar */}
              <div style={{ display: 'flex', gap: 8 }}>
                {editing ? (
                  <>
                    <ActionButton
                      onClick={saveEdit}
                      loading={saving}
                      icon={<Save size={13} />}
                      label="Save changes"
                      variant="accent"
                    />
                    <ActionButton
                      onClick={cancelEdit}
                      icon={<X size={13} />}
                      label="Cancel"
                      variant="ghost"
                    />
                  </>
                ) : (
                  <>
                    <ActionButton
                      onClick={() => updateStatus('approved')}
                      loading={saving}
                      icon={<Check size={13} />}
                      label={activeEmail?.status === 'approved' ? 'Approved ✓' : 'Approve'}
                      variant={(activeEmail?.status || currentEmail.status) === 'approved' ? 'green' : 'ghost'}
                    />
                    <ActionButton
                      onClick={() => updateStatus('rejected')}
                      loading={saving}
                      icon={<X size={13} />}
                      label="Reject"
                      variant={(activeEmail?.status || currentEmail.status) === 'rejected' ? 'red' : 'ghost'}
                    />
                    <ActionButton
                      onClick={startEdit}
                      icon={<Edit3 size={13} />}
                      label="Edit"
                      variant="ghost"
                    />
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 24, right: 24,
          background: toast.type === 'error' ? 'var(--red-dim)' : 'var(--green-dim)',
          border: `1px solid ${toast.type === 'error' ? 'rgba(239,68,68,0.3)' : 'rgba(16,185,129,0.3)'}`,
          color: toast.type === 'error' ? 'var(--red)' : 'var(--green)',
          borderRadius: 8, padding: '10px 16px', fontSize: 13, fontWeight: 500,
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
          animation: 'fadeUp 0.2s ease',
        }}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}

function StatusDot({ status }) {
  const color = status === 'approved' ? 'var(--green)'
    : status === 'rejected' ? 'var(--red)' : 'var(--t3)'
  return (
    <div style={{ width: 7, height: 7, borderRadius: '50%', background: color, flexShrink: 0 }} />
  )
}

function NavButton({ onClick, disabled, icon }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        width: 28, height: 28,
        background: 'var(--s2)', border: '1px solid var(--border)',
        borderRadius: 6, cursor: disabled ? 'not-allowed' : 'pointer',
        color: disabled ? 'var(--t3)' : 'var(--t2)',
        opacity: disabled ? 0.4 : 1,
      }}
    >
      {icon}
    </button>
  )
}

function ActionButton({ onClick, loading, icon, label, variant = 'ghost' }) {
  const styles = {
    accent: { background: 'var(--accent)', color: 'white', border: '1px solid var(--accent)' },
    green:  { background: 'var(--green-dim)', color: 'var(--green)', border: '1px solid rgba(16,185,129,0.3)' },
    red:    { background: 'var(--red-dim)', color: 'var(--red)', border: '1px solid rgba(239,68,68,0.3)' },
    ghost:  { background: 'var(--s2)', color: 'var(--t2)', border: '1px solid var(--border)' },
  }
  return (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        display: 'flex', alignItems: 'center', gap: 6,
        padding: '8px 14px', borderRadius: 7,
        fontSize: 13, fontWeight: 500,
        cursor: loading ? 'not-allowed' : 'pointer',
        fontFamily: 'Inter, sans-serif',
        opacity: loading ? 0.6 : 1,
        transition: 'all 0.15s',
        ...styles[variant],
      }}
    >
      {icon}
      {loading ? 'Saving…' : label}
    </button>
  )
}