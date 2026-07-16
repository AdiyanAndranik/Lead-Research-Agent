import { useMemo } from 'react'
import { Card } from './ui'

export default function Analytics({ leads, scores, emails }) {
  const stats = useMemo(() => {
    const total = leads.length
    const completed = leads.filter(l => !['queued', 'researching', 'scoring', 'generating_email'].includes(l.status)).length
    const failed = leads.filter(l => l.status === 'failed').length
    const skipped = leads.filter(l => l.status === 'skipped').length
    const approved = emails.filter(e => e.status === 'approved').length
    const avgScore = scores.length
      ? Math.round(scores.reduce((a, s) => a + s.overall_score, 0) / scores.length * 10) / 10
      : null
    const passRate = scores.length
      ? Math.round(scores.filter(s => s.passed_threshold).length / scores.length * 100)
      : null
    const scoreDistribution = Array.from({ length: 10 }, (_, i) => ({
      score: i + 1,
      count: scores.filter(s => s.overall_score === i + 1).length,
    }))
    const actionBreakdown = {
      prioritize: scores.filter(s => s.recommended_action === 'prioritize').length,
      nurture: scores.filter(s => s.recommended_action === 'nurture').length,
      deprioritize: scores.filter(s => s.recommended_action === 'deprioritize').length,
    }
    const timeEstimateSaved = total * 45 // ~45 min per company manually
    return { total, completed, failed, skipped, approved, avgScore, passRate, scoreDistribution, actionBreakdown, timeEstimateSaved }
  }, [leads, scores, emails])

  const maxCount = Math.max(...stats.scoreDistribution.map(d => d.count), 1)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Top stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        <StatCard label="Leads processed" value={stats.completed} total={stats.total} />
        <StatCard label="Avg lead score" value={stats.avgScore !== null ? `${stats.avgScore}/10` : '—'} />
        <StatCard label="Pass rate" value={stats.passRate !== null ? `${stats.passRate}%` : '—'} />
        <StatCard label="Time saved" value={`~${Math.round(stats.timeEstimateSaved / 60)}h`} sub="vs manual research" />
      </div>

      {/* Score distribution */}
      <Card style={{ padding: '18px 20px' }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--t2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>
          Score distribution
        </div>
        {scores.length === 0 ? (
          <div style={{ fontSize: 13, color: 'var(--t3)', textAlign: 'center', padding: '20px 0' }}>
            No scores yet.
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 80 }}>
            {stats.scoreDistribution.map(({ score, count }) => {
              const h = maxCount > 0 ? (count / maxCount) * 100 : 0
              const color = score >= 7 ? 'var(--green)' : score >= 5 ? 'var(--amber)' : 'var(--red)'
              return (
                <div key={score} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                  <div style={{ fontSize: 10, color: 'var(--t3)', minHeight: 14 }}>
                    {count > 0 ? count : ''}
                  </div>
                  <div
                    style={{
                      width: '100%', height: `${Math.max(h, count > 0 ? 8 : 2)}%`,
                      background: count > 0 ? color : 'var(--border)',
                      borderRadius: '3px 3px 0 0',
                      transition: 'height 0.4s ease',
                      opacity: count > 0 ? 1 : 0.3,
                    }}
                  />
                  <div style={{ fontSize: 10, color: 'var(--t3)', fontFamily: 'JetBrains Mono, monospace' }}>
                    {score}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Card>

      {/* Action breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
        <ActionCard label="Prioritize" count={stats.actionBreakdown.prioritize} color="var(--green)" dimColor="var(--green-dim)" />
        <ActionCard label="Nurture" count={stats.actionBreakdown.nurture} color="var(--amber)" dimColor="var(--amber-dim)" />
        <ActionCard label="Deprioritize" count={stats.actionBreakdown.deprioritize} color="var(--t3)" dimColor="var(--s2)" />
      </div>

      {/* Run summary */}
      <Card style={{ padding: '16px 20px' }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--t2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
          Run summary
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[
            { label: 'Total submitted', value: stats.total },
            { label: 'Completed', value: stats.completed },
            { label: 'Below threshold (skipped)', value: stats.skipped },
            { label: 'Failed', value: stats.failed },
            { label: 'Emails approved', value: stats.approved },
          ].map(({ label, value }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13, color: 'var(--t2)' }}>{label}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--t1)', fontFamily: 'JetBrains Mono, monospace' }}>
                {value}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

function StatCard({ label, value, total, sub }) {
  return (
    <Card style={{ padding: '14px 16px' }}>
      <div style={{ fontSize: 11, color: 'var(--t3)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: 'var(--t1)', lineHeight: 1 }}>
        {value ?? '—'}
      </div>
      {total !== undefined && (
        <div style={{ fontSize: 11, color: 'var(--t3)', marginTop: 4 }}>of {total} total</div>
      )}
      {sub && (
        <div style={{ fontSize: 11, color: 'var(--t3)', marginTop: 4 }}>{sub}</div>
      )}
    </Card>
  )
}

function ActionCard({ label, count, color, dimColor }) {
  return (
    <Card style={{ padding: '14px 16px', background: count > 0 ? dimColor : 'var(--surface)' }}>
      <div style={{ fontSize: 22, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: count > 0 ? color : 'var(--t3)', lineHeight: 1, marginBottom: 6 }}>
        {count}
      </div>
      <div style={{ fontSize: 12, color: count > 0 ? color : 'var(--t3)', fontWeight: 500 }}>
        {label}
      </div>
    </Card>
  )
}