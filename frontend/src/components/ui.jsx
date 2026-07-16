// ── Badge ──────────────────────────────────────────────────────────────────
const BADGE_STYLES = {
  green:  { background: 'var(--green-dim)',  color: 'var(--green)',  border: '1px solid rgba(16,185,129,0.25)' },
  amber:  { background: 'var(--amber-dim)',  color: 'var(--amber)',  border: '1px solid rgba(245,158,11,0.25)' },
  red:    { background: 'var(--red-dim)',    color: 'var(--red)',    border: '1px solid rgba(239,68,68,0.25)' },
  accent: { background: 'var(--accent-dim)', color: 'var(--accent)', border: '1px solid rgba(99,102,241,0.25)' },
  gray:   { background: 'rgba(90,90,114,0.15)', color: 'var(--t2)', border: '1px solid var(--border)' },
}

export function Badge({ label, variant = 'gray' }) {
  const s = BADGE_STYLES[variant] || BADGE_STYLES.gray
  return (
    <span style={{
      ...s,
      display: 'inline-flex', alignItems: 'center',
      padding: '2px 8px',
      borderRadius: 20,
      fontSize: 11,
      fontWeight: 500,
      whiteSpace: 'nowrap',
    }}>
      {label}
    </span>
  )
}

// ── StatusBadge ────────────────────────────────────────────────────────────
const STATUS_MAP = {
  queued:           { label: 'Queued',           variant: 'gray'   },
  researching:      { label: 'Researching…',     variant: 'accent' },
  scoring:          { label: 'Scoring…',         variant: 'accent' },
  generating_email: { label: 'Writing emails…',  variant: 'accent' },
  awaiting_review:  { label: 'Ready',            variant: 'green'  },
  approved:         { label: 'Approved',         variant: 'green'  },
  rejected:         { label: 'Rejected',         variant: 'red'    },
  failed:           { label: 'Failed',           variant: 'red'    },
  skipped:          { label: 'Below threshold',  variant: 'gray'   },
  running:          { label: 'Running',          variant: 'accent' },
  completed:        { label: 'Completed',        variant: 'green'  },
  pending:          { label: 'Pending',          variant: 'gray'   },
  cancelled:        { label: 'Cancelled',        variant: 'red'    },
}

export function StatusBadge({ status }) {
  const cfg = STATUS_MAP[status] || { label: status, variant: 'gray' }
  return <Badge label={cfg.label} variant={cfg.variant} />
}

// ── ScoreBar ───────────────────────────────────────────────────────────────
export function ScoreBar({ score, max = 10, animate = false }) {
  const pct = (score / max) * 100
  const color = score >= 7 ? 'var(--green)' : score >= 5 ? 'var(--amber)' : 'var(--red)'
  const trackColor = score >= 7 ? 'var(--green-dim)' : score >= 5 ? 'var(--amber-dim)' : 'var(--red-dim)'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{
        flex: 1, height: 4,
        background: trackColor,
        borderRadius: 2,
        overflow: 'hidden',
      }}>
        <div
          className={animate ? 'score-bar-fill' : ''}
          style={{
            height: '100%',
            width: `${pct}%`,
            background: color,
            borderRadius: 2,
          }}
        />
      </div>
      <span style={{ fontSize: 12, fontWeight: 600, color, fontFamily: 'JetBrains Mono, monospace', minWidth: 14 }}>
        {score}
      </span>
    </div>
  )
}

// ── Card ───────────────────────────────────────────────────────────────────
export function Card({ children, style = {}, className = '' }) {
  return (
    <div
      className={className}
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 12,
        ...style,
      }}
    >
      {children}
    </div>
  )
}

// ── Skeleton ───────────────────────────────────────────────────────────────
export function Skeleton({ width = '100%', height = 16, style = {} }) {
  return (
    <div
      className="skeleton"
      style={{ width, height, borderRadius: 4, ...style }}
    />
  )
}

// ── Divider ────────────────────────────────────────────────────────────────
export function Divider() {
  return <div style={{ height: 1, background: 'var(--border)', margin: '0' }} />
}