import { useMemo, useState } from 'react'
import { Panel } from '../components/Panel'
import { DataTable, type Column } from '../components/DataTable'
import { Seg } from '../components/Seg'
import { money } from '../lib/format'
import { generateCustomers, type Customer } from '../data/customers'

export const CUSTOMERS = generateCustomers()

type PlanFilter = 'All' | 'Starter' | 'Business' | 'Enterprise'

export function CustomersPage({ query }: { query: string }) {
  const [plan, setPlan] = useState<PlanFilter>('All')

  const rows = useMemo(() => {
    let r = CUSTOMERS
    if (plan !== 'All') r = r.filter((c) => c.plan === plan)
    if (query) r = r.filter((c) => JSON.stringify(c).toLowerCase().includes(query.toLowerCase()))
    return r
  }, [plan, query])

  const columns: Column<Customer>[] = [
    {
      key: 'name',
      label: 'Account',
      sortable: true,
      render: (c) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="av">{c.initials}</span>
          {c.name}
        </div>
      ),
    },
    {
      key: 'plan',
      label: 'Plan',
      sortable: true,
      render: (c) => <span className={`tag ${c.plan === 'Enterprise' ? 'pos' : 'dim'}`}>{c.plan}</span>,
    },
    { key: 'seats', label: 'Seats', sortable: true, numeric: true },
    { key: 'mrr', label: 'MRR', sortable: true, numeric: true, render: (c) => money(c.mrr) },
    {
      key: 'health',
      label: 'Health',
      sortable: true,
      numeric: true,
      render: (c) => <span className={c.health < 60 ? 'neg' : c.health < 80 ? 'warn' : 'pos'}>{c.health}</span>,
    },
    {
      key: 'since',
      label: 'Since',
      sortable: true,
      numeric: true,
      render: (c) => <span className="dim">{c.since}</span>,
    },
  ]

  return (
    <Panel
      title="Accounts"
      tools={
        <Seg
          id="planSeg"
          options={[
            { value: 'All', label: 'All' },
            { value: 'Starter', label: 'Starter' },
            { value: 'Business', label: 'Business' },
            { value: 'Enterprise', label: 'Enterprise' },
          ]}
          value={plan}
          onChange={setPlan}
        />
      }
    >
      <DataTable<Customer>
        columns={columns}
        rows={rows}
        rowKey={(c) => c.name}
        defaultSort={{ key: 'mrr', type: 'n' }}
        empty={<span>No accounts match &ldquo;{query}&rdquo;</span>}
      />
    </Panel>
  )
}