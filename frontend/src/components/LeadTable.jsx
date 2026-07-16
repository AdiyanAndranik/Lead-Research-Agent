import {
  useReactTable, getCoreRowModel, getSortedRowModel,
  getFilteredRowModel, flexRender,
} from '@tanstack/react-table'
import { useState, useMemo } from 'react'
import { StatusBadge, ScoreBar } from './ui'
import { ArrowUpDown, ArrowUp, ArrowDown, Search } from 'lucide-react'

const STATUS_OPTIONS = [
  'all', 'awaiting_review', 'approved', 'rejected', 'skipped', 'failed'
]

export default function LeadTable({ leads, scores }) {
  const [sorting, setSorting] = useState([])
  const [statusFilter, setStatusFilter] = useState('all')
  const [search, setSearch] = useState('')

  // Merge scores into leads
  const data = useMemo(() => {
    const scoreMap = Object.fromEntries(scores.map(s => [s.company_name, s]))
    return leads
      .map(lead => ({
        ...lead,
        score: scoreMap[lead.company_name]?.overall_score ?? null,
        recommended_action: scoreMap[lead.company_name]?.recommended_action ?? null,
        industry: scoreMap[lead.company_name]?.industry ?? null,
      }))
      .filter(lead => {
        if (statusFilter !== 'all' && lead.status !== statusFilter) return false
        if (search && !lead.company_name.toLowerCase().includes(search.toLowerCase())) return false
        return true
      })
  }, [leads, scores, statusFilter, search])

  const columns = useMemo(() => [
    {
      accessorKey: 'company_name',
      header: 'Company',
      cell: ({ row }) => (
        <div>
          <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--t1)' }}>
            {row.original.company_name}
          </div>
          <div style={{ fontSize: 11, color: 'var(--t3)', fontFamily: 'JetBrains Mono, monospace', marginTop: 2 }}>
            {row.original.domain || '—'}
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ getValue }) => <StatusBadge status={getValue()} />,
    },
    {
      accessorKey: 'score',
      header: 'Score',
      cell: ({ getValue }) => {
        const score = getValue()
        return score !== null ? (
          <div style={{ width: 120 }}>
            <ScoreBar score={score} />
          </div>
        ) : <span style={{ color: 'var(--t3)', fontSize: 12 }}>—</span>
      },
    },
    {
      accessorKey: 'recommended_action',
      header: 'Action',
      cell: ({ getValue }) => {
        const v = getValue()
        if (!v) return <span style={{ color: 'var(--t3)', fontSize: 12 }}>—</span>
        const color = v === 'prioritize' ? 'var(--green)'
          : v === 'nurture' ? 'var(--amber)' : 'var(--t3)'
        return <span style={{ fontSize: 12, color, fontWeight: 500, textTransform: 'capitalize' }}>{v}</span>
      },
    },
    {
      accessorKey: 'created_at',
      header: 'Added',
      cell: ({ getValue }) => (
        <span style={{ fontSize: 12, color: 'var(--t3)', fontFamily: 'JetBrains Mono, monospace' }}>
          {new Date(getValue()).toLocaleDateString()}
        </span>
      ),
    },
  ], [])

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  return (
    <div>
      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
          <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--t3)' }} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search companies…"
            style={{
              width: '100%',
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 7, padding: '7px 10px 7px 30px',
              fontSize: 13, color: 'var(--t1)', fontFamily: 'Inter, sans-serif',
              outline: 'none',
            }}
          />
        </div>

        {/* Status filter */}
        <div style={{ display: 'flex', gap: 4 }}>
          {STATUS_OPTIONS.map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              style={{
                padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 500,
                background: statusFilter === s ? 'var(--accent-dim)' : 'var(--surface)',
                border: `1px solid ${statusFilter === s ? 'rgba(99,102,241,0.3)' : 'var(--border)'}`,
                color: statusFilter === s ? 'var(--accent)' : 'var(--t2)',
                cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                transition: 'all 0.15s', textTransform: 'capitalize',
              }}
            >
              {s === 'all' ? 'All' : s.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div style={{
        background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: 10, overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id} style={{ borderBottom: '1px solid var(--border)' }}>
                {hg.headers.map(header => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    style={{
                      padding: '10px 16px', textAlign: 'left',
                      fontSize: 11, fontWeight: 600,
                      color: 'var(--t3)', textTransform: 'uppercase', letterSpacing: '0.05em',
                      cursor: header.column.getCanSort() ? 'pointer' : 'default',
                      userSelect: 'none', whiteSpace: 'nowrap',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getCanSort() && (
                        <span style={{ color: 'var(--t3)' }}>
                          {header.column.getIsSorted() === 'asc' ? <ArrowUp size={11} />
                            : header.column.getIsSorted() === 'desc' ? <ArrowDown size={11} />
                            : <ArrowUpDown size={11} />}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: '40px', textAlign: 'center', color: 'var(--t3)', fontSize: 13 }}>
                  No leads match the current filter.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row, i) => (
                <tr
                  key={row.id}
                  style={{
                    borderBottom: i < table.getRowModel().rows.length - 1 ? '1px solid var(--border)' : 'none',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--s2)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} style={{ padding: '12px 16px' }}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ fontSize: 12, color: 'var(--t3)', marginTop: 10, textAlign: 'right' }}>
        {data.length} lead{data.length !== 1 ? 's' : ''} shown
      </div>
    </div>
  )
}