import { rng } from '../lib/rng'
import { type Plan, PLANS, customerName } from './seed'

export interface Customer {
  name: string
  initials: string
  plan: Plan
  seats: number
  mrr: number
  since: number
  health: number
}

export function generateCustomers(count = 34): Customer[] {
  return Array.from({ length: count }, () => {
    const { name, initials } = customerName()
    return {
      name,
      initials,
      plan: PLANS[Math.floor(rng() * PLANS.length)] as Plan,
      seats: Math.round(3 + rng() * 240),
      mrr: Math.round((90 + rng() * 3400) / 10) * 10,
      since: 2021 + Math.floor(rng() * 5),
      health: Math.round(42 + rng() * 58),
    }
  })
}
