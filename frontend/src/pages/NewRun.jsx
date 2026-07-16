import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ingestText, ingestCSV } from '../api/client'
import { Play, Upload, ArrowLeft, AlertCircle } from 'lucide-react'
import { Card } from '../components/ui'

const INPUT_STYLE = {
  width: '100%',
  background: 'var(--s2)',
  border: '1px solid var(--border)',
  borderRadius: 8,
  padding: '8px 12px',
  fontSize: 13,
  color: 'var(--t1)',
  fontFamily: 'Inter, sans-serif',
  outline: 'none',
  transition: 'border-color 0.15s',
}

const LABEL_STYLE = {
  display: 'block',
  fontSize: 12,
  fontWeight: 500,
  color: 'var(--t2)',
  marginBottom: 6,
}

export default function NewRun() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('text')
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [config, setConfig] = useState({
    min_score_threshold: 6,
    email_tone: 'conversational',
    email_angle: 'pain',
    target_company_size: 'any',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const cfg = (key, val) => setConfig(c => ({ ...c, [key]: val }))

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    try {
      let res
      if (mode === 'text') {
        res = await ingestText(text, config)
      } else {
        res = await ingestCSV(file, config)
      }
      const runId = res.data.pipeline_run_id
      if (runId) {
        const runs = JSON.parse(localStorage.getItem('pipeline_runs') || '[]')
        runs.unshift({
          id: runId,
          total: res.data.validation.total_accepted,
          status: 'running',
          created_at: new Date().toLocaleString(),
        })
        localStorage.setItem('pipeline_runs', JSON.stringify(runs.slice(0, 20)))
        navigate(`/runs/${runId}`)
      } else {
        setError('No valid leads found — check your input and try again.')
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Request failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const canSubmit = mode === 'text' ? text.trim().length > 0 : file !== null

  return (
    <div style={{ padding: '40px 48px', maxWidth: 680, margin: '0 auto' }} className="fade-up">
      {/* Back */}
      <Link
        to="/"
        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--t3)', fontSize: 13, textDecoration: 'none', marginBottom: 24 }}
      >
        <ArrowLeft size={13} /> Back
      </Link>

      <h1 style={{ fontSize: 22, fontWeight: 600, color: 'var(--t1)', margin: '0 0 4px' }}>
        New pipeline run
      </h1>
      <p style={{ color: 'var(--t2)', fontSize: 13, margin: '0 0 32px' }}>
        Submit companies to research, score, and generate outreach emails.
      </p>

      {/* Input mode toggle */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: 4 }}>
        {[{ id: 'text', label: 'Plain text' }, { id: 'csv', label: 'CSV upload' }].map(m => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            style={{
              flex: 1, padding: '7px 12px',
              background: mode === m.id ? 'var(--s2)' : 'transparent',
              border: mode === m.id ? '1px solid var(--border)' : '1px solid transparent',
              borderRadius: 6, fontSize: 13, fontWeight: 500,
              color: mode === m.id ? 'var(--t1)' : 'var(--t2)',
              cursor: 'pointer', fontFamily: 'Inter, sans-serif',
              transition: 'all 0.15s',
            }}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Input area */}
      {mode === 'text' ? (
        <Card style={{ marginBottom: 20 }}>
          <div style={{ padding: 16 }}>
            <label style={LABEL_STYLE}>Company list</label>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              rows={7}
              placeholder={"Linear, linear.app\nStripe, stripe.com\nhttps://retool.com\nNotion"}
              style={{
                ...INPUT_STYLE,
                resize: 'vertical',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: 12,
                lineHeight: 1.7,
              }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
            <p style={{ fontSize: 11, color: 'var(--t3)', margin: '8px 0 0' }}>
              One per line — names, URLs, LinkedIn URLs, or any mix.
            </p>
          </div>
        </Card>
      ) : (
        <Card style={{ marginBottom: 20 }}>
          <div
            style={{
              padding: 32,
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              cursor: 'pointer', textAlign: 'center',
              border: '2px dashed var(--border)',
              borderRadius: 10, margin: 8,
              transition: 'border-color 0.15s',
            }}
            onClick={() => document.getElementById('csv-input').click()}
            onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent)'}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <Upload size={22} color="var(--t3)" style={{ marginBottom: 10 }} />
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--t2)', marginBottom: 4 }}>
              {file ? file.name : 'Click to upload CSV'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--t3)' }}>
              Accepts: company, url, linkedin columns
            </div>
          </div>
          <input id="csv-input" type="file" accept=".csv" style={{ display: 'none' }} onChange={e => setFile(e.target.files[0])} />
        </Card>
      )}

      {/* Config */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)' }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--t2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Config
          </span>
        </div>
        <div style={{ padding: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label style={LABEL_STYLE}>Min score threshold</label>
            <input
              type="number" min={1} max={10}
              value={config.min_score_threshold}
              onChange={e => cfg('min_score_threshold', +e.target.value)}
              style={INPUT_STYLE}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>
          <div>
            <label style={LABEL_STYLE}>Email tone</label>
            <Select value={config.email_tone} onChange={v => cfg('email_tone', v)} options={[
              { value: 'conversational', label: 'Conversational' },
              { value: 'formal', label: 'Formal' },
              { value: 'brief', label: 'Brief' },
            ]} />
          </div>
          <div>
            <label style={LABEL_STYLE}>Email angle</label>
            <Select value={config.email_angle} onChange={v => cfg('email_angle', v)} options={[
              { value: 'pain', label: 'Pain first' },
              { value: 'opportunity', label: 'Opportunity first' },
              { value: 'social_proof', label: 'Social proof first' },
            ]} />
          </div>
          <div>
            <label style={LABEL_STYLE}>Company size</label>
            <Select value={config.target_company_size} onChange={v => cfg('target_company_size', v)} options={[
              { value: 'any', label: 'Any size' },
              { value: 'startup', label: 'Startup (1–50)' },
              { value: 'scaleup', label: 'Scaleup (50–300)' },
              { value: 'mid', label: 'Mid-market (300–1000)' },
            ]} />
          </div>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 10,
          background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.25)',
          borderRadius: 8, padding: '12px 14px', marginBottom: 16,
          color: 'var(--red)', fontSize: 13,
        }}>
          <AlertCircle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
          {error}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading || !canSubmit}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          background: canSubmit && !loading ? 'var(--accent)' : 'var(--s2)',
          color: canSubmit && !loading ? 'white' : 'var(--t3)',
          border: 'none', borderRadius: 8, padding: '12px 20px',
          fontSize: 14, fontWeight: 500, cursor: canSubmit && !loading ? 'pointer' : 'not-allowed',
          fontFamily: 'Inter, sans-serif', transition: 'all 0.15s',
        }}
      >
        <Play size={14} fill={canSubmit && !loading ? 'white' : 'var(--t3)'} />
        {loading ? 'Launching pipeline…' : 'Run pipeline'}
      </button>
    </div>
  )
}

function Select({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        width: '100%',
        background: 'var(--s2)',
        border: '1px solid var(--border)',
        borderRadius: 8, padding: '8px 12px',
        fontSize: 13, color: 'var(--t1)',
        fontFamily: 'Inter, sans-serif', outline: 'none',
        cursor: 'pointer',
      }}
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  )
}