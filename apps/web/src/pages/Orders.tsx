import { useMemo, useState } from 'react'
import { Panel } from '../components/Panel'
import { DataTable, type Column } from '../components/DataTable'
import { Seg } from '../components/Seg'
import { money } from '../lib/format'
import { toast } from '../components/ui'
import { generateOrders, type Order } from '../data/orders'

export const ORDERS = generateOrders()

type StatusFilter = 'All' | 'Paid' | 'Pending' | 'Refunded'

const statusTone: Record<string, 'pos' | 'warn' | 'neg'> = {
  Paid: 'pos',
  Pending: 'warn',
  Refunded: 'neg',
}

function exportCsv(rows: Order[]) {
  const header = ['Order', 'Customer', 'Market', 'Date', 'Status', 'Total']
  const body = rows.map((r) => [r.id, r.customer, r.city, r.date, r.status, r.total].join(','))
  const csv = [header.join(','), ...body].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'orders.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export function OrdersPage({ query, status }: { query: string; status: StatusFilter }) {
  const [page, setPage] = useState(1)

  const rows = useMemo(() => {
    let r = ORDERS
    if (status !== 'All') r = r.filter((o) => o.status === status)
    if (query) r = r.filter((o) => JSON.stringify(o).toLowerCase().includes(query.toLowerCase()))
    return r
  }, [status, query])

  const columns: Column<Order>[] = [
    { key: 'id', label: 'Order', sortable: true },
    {
      key: 'customer',
      label: 'Customer',
      sortable: true,
      render: (o) => (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
          <span className="av">{o.initials}</span>
          {o.customer}
        </span>
      ),
    },
    { key: 'date', label: 'Date', sortable: true },
    {
      key: 'status',
      label: 'Status',
      sortable: true,
      render: (o) => <span className={`status ${statusTone[o.status] ?? ''}`}>{o.status}</span>,
    },
    { key: 'total', label: 'Total', sortable: true, numeric: true, render: (o) => money(o.total) },
  ]

  return (
    <Panel
      title="Orders"
      tools={
        <>
          <Seg
            id="statSeg"
            options={[
              { value: 'All', label: 'All' },
              { value: 'Paid', label: 'Paid' },
              { value: 'Pending', label: 'Pending' },
              { value: 'Refunded', label: 'Refunded' },
            ]}
            value={status}
            onChange={() => setPage(1)}
          />
          <button
            type="button"
            className="btn"
            onClick={() => {
              exportCsv(rows)
              toast('Exported orders to CSV')
            }}
          >
            Export CSV
          </button>
        </>
      }
    >
      <DataTable<Order>
        columns={columns}
        rows={rows}
        rowKey={(o) => o.id}
        page={page}
        onPage={setPage}
        pageSize={8}
        defaultSort={{ key: 'date', type: 's', dir: 'desc' }}
        empty="No orders match your filters"
      />
    </Panel>
  )
}
