import { useMemo, useState } from 'react'
import { Panel } from '../components/Panel'
import { DataTable, type Column } from '../components/DataTable'
import { EChart } from '../lib/chart'
import { cssVar } from '../lib/theme'
import { money } from '../lib/format'
import { generateInvoices, type Invoice } from '../data/invoices'

export const INVOICES = generateInvoices()

const stateTone: Record<string, 'pos' | 'warn' | 'neg'> = {
  Current: 'pos',
  Due: 'warn',
  Overdue: 'neg',
}

export function InvoicesPage({ query }: { query: string }) {
  const [page, setPage] = useState(1)

  const aging = useMemo(() => {
    const labels = ['0–20d', '21–45d', '46–60d', '60d+']
    const totals = [0, 0, 0, 0]
    for (const inv of INVOICES) {
      const idx = inv.age <= 20 ? 0 : inv.age <= 45 ? 1 : inv.age <= 60 ? 2 : 3
      totals[idx]! += inv.amount
    }
    return { labels, totals }
  }, [])

  const rows = useMemo(() => {
    if (!query) return INVOICES
    return INVOICES.filter((i) => JSON.stringify(i).toLowerCase().includes(query.toLowerCase()))
  }, [query])

  const columns: Column<Invoice>[] = [
    { key: 'id', label: 'Invoice', sortable: true },
    { key: 'customer', label: 'Customer', sortable: true },
    { key: 'age', label: 'Days', sortable: true, numeric: true, render: (i) => `${i.age}d` },
    {
      key: 'state',
      label: 'State',
      sortable: true,
      render: (i) => <span className={`status ${stateTone[i.state] ?? ''}`}>{i.state}</span>,
    },
    { key: 'amount', label: 'Amount', sortable: true, numeric: true, render: (i) => money(i.amount) },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <Panel title="All invoices">
        <DataTable<Invoice>
          columns={columns}
          rows={rows}
          rowKey={(i) => i.id}
          page={page}
          onPage={setPage}
          pageSize={8}
          defaultSort={{ key: 'age', type: 'n', dir: 'desc' }}
          empty="No invoices match your filters"
        />
      </Panel>
      <Panel title="Aging">
        <EChart
          id="ageChart"
          style={{ height: '242px' }}
          build={() => ({
            grid: { left: 52, right: 16, top: 12, bottom: 22 },
            tooltip: { trigger: 'axis', valueFormatter: (v: unknown) => money(Number(v)) },
            xAxis: { type: 'category', data: aging.labels },
            yAxis: {
              type: 'value',
              splitLine: { show: false },
              axisLabel: {
                color: cssVar('--faint'),
                fontSize: 10.5,
                fontFamily: cssVar('--mono'),
                formatter: (v: number) => `$${Math.round(v / 1000)}k`,
              },
            },
            series: [
              {
                type: 'bar',
                data: aging.totals,
                barWidth: '46%',
                itemStyle: {
                  borderRadius: [2, 2, 0, 0],
                  color: (p: { dataIndex: number }) =>
                    [cssVar('--accent'), cssVar('--accent'), cssVar('--warn'), cssVar('--neg')][p.dataIndex],
                },
              },
            ],
          })}
        />
      </Panel>
    </div>
  )
}
