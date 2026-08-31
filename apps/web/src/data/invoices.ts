import { rng } from '../lib/rng'
import { type Customer, generateCustomers } from './customers'

export type InvoiceState = 'Current' | 'Due' | 'Overdue'

export interface Invoice {
  id: string
  customer: string
  age: number
  state: InvoiceState
  amount: number
}

const customers: Customer[] = generateCustomers()

function stateFor(age: number): InvoiceState {
  if (age > 45) return 'Overdue'
  if (age > 20) return 'Due'
  return 'Current'
}

export function generateInvoices(count = 22): Invoice[] {
  return Array.from({ length: count }, (_, i) => {
    const c = customers[Math.floor(rng() * customers.length)]!
    const age = Math.round(rng() * 74)
    return {
      id: `INV-${2240 - i}`,
      customer: c.name,
      age,
      state: stateFor(age),
      amount: Math.round((300 + rng() * 9000) / 10) * 10,
    }
  })
}

export type AgingBucket = { label: string; count: number }

export function agingBuckets(invoices: Invoice[]): AgingBucket[] {
  const counts: AgingBucket[] = [
    { label: '0–20d', count: 0 },
    { label: '21–45d', count: 0 },
    { label: '46–60d', count: 0 },
    { label: '60d+', count: 0 },
  ]
  for (const inv of invoices) {
    if (inv.age <= 20) counts[0]!.count++
    else if (inv.age <= 45) counts[1]!.count++
    else if (inv.age <= 60) counts[2]!.count++
    else counts[3]!.count++
  }
  return counts
}
