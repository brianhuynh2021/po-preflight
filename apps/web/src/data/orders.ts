import { rng, pick } from '../lib/rng'
import { generateCustomers } from './customers'
import { ORDER_STATUSES, CITIES, type OrderStatus } from './seed'

export interface Order {
  id: string
  customer: string
  initials: string
  date: string
  status: OrderStatus
  city: string
  total: number
}

const customers = generateCustomers()

export function generateOrders(count = 132): Order[] {
  return Array.from({ length: count }, (_, i) => {
    const c = customers[Math.floor(rng() * customers.length)]!
    // Spread dates backwards from 2026-07-15.
    const d = new Date(Date.UTC(2026, 7, 15 - Math.floor(i / 6.6)))
    return {
      id: `NW-${7420 - i}`,
      customer: c.name,
      initials: c.initials,
      date: d.toISOString().slice(0, 10),
      status: pick(ORDER_STATUSES),
      city: pick(CITIES),
      total: Math.round((40 + rng() * 1900) / 5) * 5,
    }
  })
}

export interface Hotspot {
  city: string
  v: number
  pin: boolean
}

// Aggregate order totals per city for the world map hotspots.
export function ordersByCity(orders: Order[], pinCity?: string): Hotspot[] {
  const sums = new Map<string, number>()
  for (const o of orders) {
    sums.set(o.city, (sums.get(o.city) || 0) + o.total)
  }
  return Array.from(sums.entries())
    .map(([city, total]) => ({ city, v: Math.round(total / 100), pin: city === pinCity }))
    .sort((a, b) => b.v - a.v)
}
