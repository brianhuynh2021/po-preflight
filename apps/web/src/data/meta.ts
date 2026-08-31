// Cross-cutting meta data: KPIs, activity feed, notifications, saved reports,
// and analytics chart datasets.

export type Tone = 'pos' | 'neg' | 'warn' | 'accent'

export interface Kpi {
  lbl: string
  to: number
  d: number
  money?: boolean
  pct?: boolean
  goodDown?: boolean
}

export const KPIS: Kpi[] = [
  { lbl: 'Revenue', to: 284310, d: 12.4, money: true },
  { lbl: 'Orders', to: 3842, d: 6.1 },
  { lbl: 'Active users', to: 18204, d: 3.8 },
  { lbl: 'Refund rate', to: 2.1, d: 0.4, pct: true, goodDown: true },
]

// KPI sparklines (sample series).
export const KPI_SPARKS: number[][] = [
  [120, 138, 121, 156, 148, 170, 162, 180, 196, 188, 210, 231],
  [60, 74, 71, 82, 79, 88, 92, 101, 97, 112, 109, 124],
  [90, 84, 102, 96, 112, 120, 116, 130, 128, 141, 148, 156],
  [4.2, 3.9, 4.0, 3.6, 3.8, 3.3, 3.5, 3.1, 3.2, 2.8, 2.6, 2.1],
]

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// Revenue over time with two series (30 / 90 / 12 months). Mirrors the
// reference generator: values scale by step (30d/90d/12m), labels are short
// month (+ day for sub-monthly buckets).
function seeded(seed: number): () => number {
  let a = seed >>> 0
  return () => {
    a = (a * 1664525 + 1013904223) >>> 0
    return a / 4294967296
  }
}

export function revenueSeries(range: '30d' | '90d' | '12m'): {
  labels: string[]
  current: number[]
  previous: number[]
} {
  const days = range === '12m' ? 365 : range === '90d' ? 90 : 30
  const t = days > 180 ? 30 : days > 45 ? 7 : 1
  const a = Math.round(days / t)
  const rnd = seeded(424242 + days)
  let n = 6200
  let i = 5400
  const current: number[] = []
  const previous: number[] = []
  const labels: string[] = []
  for (let u = 0; u < a; u++) {
    n = Math.max(2600, n + (rnd() - 0.43) * 900 * (t > 1 ? 2.4 : 1))
    i = Math.max(2300, i + (rnd() - 0.47) * 820 * (t > 1 ? 2.4 : 1))
    current.push(Math.round(n * t * 0.38))
    previous.push(Math.round(i * t * 0.38))
    const c = new Date(Date.UTC(2026, 7, 15))
    c.setUTCDate(c.getUTCDate() - (a - u) * t)
    labels.push(
      t > 20
        ? c.toLocaleString('en', { month: 'short', timeZone: 'UTC' })
        : c.toLocaleString('en', { month: 'short', day: 'numeric', timeZone: 'UTC' }),
    )
  }
  return { labels, current, previous }
}

// Traffic sources (donut).
export const TRAFFIC_SOURCES: [string, number][] = [
  ['Organic search', 41.2],
  ['Direct', 24.8],
  ['Referral', 16.3],
  ['Paid social', 11.4],
  ['Email', 6.3],
]
export const TRAFFIC_TOTAL = 18204

// Acquisition funnel.
export const FUNNEL: [string, number][] = [
  ['Visited', 18204],
  ['Signed up', 5410],
  ['Activated', 2980],
  ['Subscribed', 1240],
  ['Retained 90d', 918],
]

// Weekly cohort retention heatmap: 8 weeks x 7 plus labels.
export const COHORT_WEEKS = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8']
export const COHORT_DAYS = ['D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6']
export const COHORT_ROWS: number[][] = [
  [100, 62, 48, 41, 36, 32, 29],
  [100, 58, 45, 39, 34, 31, 28],
  [100, 61, 46, 40, 35, 33, 30],
  [100, 59, 44, 38, 34, 30, 27],
  [100, 63, 49, 42, 37, 34, 31],
  [100, 60, 47, 41, 36, 32, 29],
  [100, 62, 48, 40, 35, 31, 28],
  [100, 57, 43, 37, 33, 29, 26],
]

// Channel table (analytics).
export interface Channel {
  channel: string
  sessions: number
  signups: number
  cvr: number
  cac: number
}
export const CHANNELS: Channel[] = [
  { channel: 'Organic search', sessions: 7421, signups: 2380, cvr: 32.1, cac: 18 },
  { channel: 'Direct', sessions: 4516, signups: 1110, cvr: 24.6, cac: 0 },
  { channel: 'Referral', sessions: 2967, signups: 842, cvr: 28.4, cac: 22 },
  { channel: 'Paid social', sessions: 2075, signups: 498, cvr: 24.0, cac: 41 },
  { channel: 'Email', sessions: 1225, signups: 580, cvr: 47.3, cac: 12 },
]

// Activity feed + notifications.
export interface Activity {
  title: string
  detail: string
  tone: Tone
  time: string
}
export const ACTIVITY: Activity[] = [
  { title: 'Refund issued', detail: 'NW-7402 · $1,240 · Maya Okafor', tone: 'neg', time: '11m' },
  { title: 'New enterprise order', detail: 'Pallas floor mat × 480 · Petra Novak', tone: 'pos', time: '34m' },
  { title: 'Stock below reorder', detail: 'Quill notebook set · 32 remaining', tone: 'warn', time: '1h' },
  { title: 'Invoice overdue', detail: 'INV-2231 · Chen Haddad', tone: 'neg', time: '2h' },
  { title: 'Shipment delivered', detail: 'NW-7360 · Lisbon', tone: 'pos', time: '3h' },
  { title: 'Review flagged', detail: 'Orbit wall clock · 1 star', tone: 'warn', time: '5h' },
  { title: 'Subscription upgraded', detail: 'Arabella Soto → Business', tone: 'accent', time: '6h' },
  { title: 'Warehouse restocked', detail: '+1,200 units across 6 SKUs', tone: 'pos', time: '8h' },
]

export interface Notification {
  title: string
  detail: string
  tone: Tone
  time: string
  read?: boolean
}
export const NOTIFICATIONS: Notification[] = [
  { title: 'Refund issued', detail: 'NW-7402 · $1,240 · Maya Okafor', tone: 'neg', time: '11m' },
  { title: 'New enterprise order', detail: 'Pallas floor mat × 480', tone: 'pos', time: '34m' },
  { title: 'Stock below reorder', detail: 'Quill notebook set · 32 remaining', tone: 'warn', time: '1h' },
  { title: 'Invoice overdue', detail: 'INV-2231 · Chen Haddad', tone: 'neg', time: '2h' },
  { title: 'Shipment delivered', detail: 'NW-7360 · Lisbon', tone: 'pos', time: '3h' },
]

// Saved reports.
export interface SavedReport {
  name: string
  schedule: string
  slug: string
}
export const SAVED_REPORTS: SavedReport[] = [
  { name: 'Monthly revenue recap', schedule: 'Scheduled · 1st of month', slug: 'revenue' },
  { name: 'Refund reasons', schedule: 'Manual', slug: 'refunds' },
  { name: 'Enterprise pipeline', schedule: 'Scheduled · Mondays', slug: 'pipeline' },
  { name: 'Churn by plan', schedule: 'Manual', slug: 'churn' },
  { name: 'Inventory turns', schedule: 'Manual', slug: 'inventory' },
  { name: 'Support load vs orders', schedule: 'Manual', slug: 'support' },
]

// Recent orders for the Dashboard table (reuse the orders module via prop).
