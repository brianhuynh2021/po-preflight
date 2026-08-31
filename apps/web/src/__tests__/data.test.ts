import { generateCustomers } from '../data/customers'
import { generateOrders, ordersByCity } from '../data/orders'
import { generateProducts } from '../data/products'
import { generateInvoices, agingBuckets } from '../data/invoices'
import { mulberry32 } from '../lib/rng'
import { PLANS, CITIES } from '../data/seed'

describe('seeded RNG', () => {
  it('is deterministic for a fixed seed', () => {
    const a = mulberry32(20260815)
    const b = mulberry32(20260815)
    for (let i = 0; i < 50; i++) {
      expect(a()).toBe(b())
    }
  })

  it('produces values in the unit interval', () => {
    const next = mulberry32(20260815)
    for (let i = 0; i < 100; i++) {
      const v = next()
      expect(v).toBeGreaterThanOrEqual(0)
      expect(v).toBeLessThan(1)
    }
  })
})

describe('customers', () => {
  const customers = generateCustomers()

  it('generates the contract number of customers', () => {
    expect(customers).toHaveLength(34)
  })

  it('matches the contract field shapes', () => {
    const c = customers[0]!
    expect(typeof c.name).toBe('string')
    expect(c.name).toMatch(/\w+ \w+/)
    expect(c.initials).toMatch(/^[A-Z][A-Z]$/)
    expect(PLANS).toContain(c.plan)
    expect(c.seats).toBeGreaterThanOrEqual(3)
    expect(c.mrr).toBeGreaterThanOrEqual(90)
    expect(Number.isInteger(c.mrr)).toBe(true)
    expect(c.since).toBeGreaterThanOrEqual(2021)
    expect(c.since).toBeLessThanOrEqual(2025)
    expect(c.health).toBeGreaterThanOrEqual(42)
    expect(c.health).toBeLessThanOrEqual(100)
  })
})

describe('orders', () => {
  const orders = generateOrders()

  it('generates the contract number of orders', () => {
    expect(orders).toHaveLength(132)
  })

  it('matches the contract field shapes', () => {
    const o = orders[0]!
    expect(o.id).toMatch(/^NW-\d+$/)
    expect(typeof o.customer).toBe('string')
    expect(o.date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(['Paid', 'Pending', 'Refunded']).toContain(o.status)
    expect(CITIES).toContain(o.city)
    expect(o.total).toBeGreaterThanOrEqual(40)
    expect(typeof o.total).toBe('number')
  })

  it('spreads order IDs in descending sequence', () => {
    expect(orders[0]!.id).toBe('NW-7420')
    expect(orders[131]!.id).toBe('NW-7289')
  })
})

describe('ordersByCity', () => {
  const orders = generateOrders(10).map((o, i) => ({
    ...o,
    city: i % 2 === 0 ? 'Rome' : 'Madrid',
    total: 100,
  }))

  it('aggregates order totals per city and sorts by volume descending', () => {
    const hot = ordersByCity(orders)
    expect(hot.map((h) => h.city)).toEqual(['Rome', 'Madrid'])
    expect(hot[0]!.v).toBe(5)
    expect(hot[1]!.v).toBe(5)
  })

  it('marks the pinned city', () => {
    const hot = ordersByCity(orders, 'Madrid')
    expect(hot.find((h) => h.city === 'Madrid')!.pin).toBe(true)
    expect(hot.find((h) => h.city === 'Rome')!.pin).toBe(false)
  })
})

describe('products', () => {
  const products = generateProducts()

  it('generates the contract number of products', () => {
    expect(products).toHaveLength(10)
  })

  it('matches the contract field shapes', () => {
    const p = products[0]!
    expect(typeof p.name).toBe('string')
    expect(p.sku).toMatch(/^SKU-\d+$/)
    expect(p.stock).toBeGreaterThanOrEqual(0)
    expect(p.reorder).toBeGreaterThanOrEqual(40)
    expect(p.sold).toBeGreaterThanOrEqual(60)
    expect(p.price).toBeGreaterThanOrEqual(18)
  })
})

describe('invoices', () => {
  const invoices = generateInvoices()

  it('generates the contract number of invoices', () => {
    expect(invoices).toHaveLength(22)
  })

  it('matches the contract field shapes and derives state from age', () => {
    for (const inv of invoices) {
      expect(inv.id).toMatch(/^INV-\d+$/)
      expect(['Current', 'Due', 'Overdue']).toContain(inv.state)
      expect(inv.amount).toBeGreaterThanOrEqual(300)
      if (inv.age > 45) expect(inv.state).toBe('Overdue')
      else if (inv.age > 20) expect(inv.state).toBe('Due')
      else expect(inv.state).toBe('Current')
    }
  })

  it('aging buckets cover every invoice exactly once', () => {
    const total = agingBuckets(invoices).reduce((sum, b) => sum + b.count, 0)
    expect(total).toBe(invoices.length)
  })
})
