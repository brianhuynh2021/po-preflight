import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, within, cleanup } from '@testing-library/react'
import App from '../App'
import { PAGE_KEYS, PAGE_TITLES } from '../pages'
import { ORDERS } from '../pages/Orders'
import { CUSTOMERS } from '../pages/Customers'
import { SAVED_REPORTS } from '../data/meta'
import { ErrorBoundary } from '../components/ErrorBoundary'

// Auto-inflate so the Dashboard chart/count-up animations do not loop forever in
// jsdom. onTick is driven synchronously in tests where it matters.
beforeEach(() => {
  vi.spyOn(window, 'requestAnimationFrame').mockImplementation(() => 0)
  vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => {})
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

function navButtons() {
  const nav = document.getElementById('nav')
  return nav ? within(nav).getAllByRole('button') : []
}

function goto(pageLabel: string) {
  const btn = navButtons().find((b) => b.textContent?.includes(pageLabel))
  expect(btn).toBeTruthy()
  fireEvent.click(btn!)
}

describe('App sidebar navigation (US1)', () => {
  it('renders all eight sidebar pages', () => {
    render(<App />)
    const labels = navButtons().map((b) => b.textContent ?? '')
    for (const key of PAGE_KEYS) {
      expect(labels.some((l) => l.includes(PAGE_TITLES[key]))).toBe(true)
    }
    expect(navButtons()).toHaveLength(8)
  })

  it('switches the active page and highlights it on click', () => {
    render(<App />)
    for (const key of PAGE_KEYS) {
      goto(PAGE_TITLES[key])
      // Header reflects the active page.
      expect(document.getElementById('title')?.textContent).toBe(PAGE_TITLES[key])
      // Active nav item is highlighted.
      const active = navButtons().find((b) => b.className.includes('on'))
      expect(active?.textContent).toContain(PAGE_TITLES[key])
    }
  })

  it('renders rea content on Customers and Settings pages', () => {
    render(<App />)
    goto('Customers')
    expect(screen.getByText('Accounts')).toBeInTheDocument()
    goto('Settings')
    expect(screen.getByText('Appearance')).toBeInTheDocument()
  })

  it('shows the entire customer dataset without pagination', () => {
    render(<App />)
    goto('Customers')

    const tfoot = document.querySelector('.tfoot')
    expect(tfoot).not.toBeInTheDocument()
    const rows = document.querySelectorAll('tbody tr')
    expect(rows.length).toBe(CUSTOMERS.length)
  })
})

describe('Orders sortable table (US3)', () => {
  it('sorts the orders table by Total numerically', () => {
    render(<App />)
    goto('Orders')

    const totalTh = screen.getByText('Total').closest('th') as HTMLTableCellElement
    fireEvent.click(screen.getByText('Total'))

    expect(totalTh.getAttribute('data-dir')).toBe('asc')
    const firstRow = document.querySelector('tbody tr') as HTMLTableRowElement
    const firstId = (firstRow?.querySelector('td') as HTMLTableCellElement)?.textContent?.trim()

    const sortedAsc = [...ORDERS].sort((a, b) => a.total - b.total)
    expect(firstId).toBe(sortedAsc[0]!.id)
  })

  it('sorts the orders table by Customer alphabetically', () => {
    render(<App />)
    goto('Orders')

    fireEvent.click(screen.getByText('Customer'))
    const firstRow = document.querySelector('tbody tr') as HTMLTableRowElement
    const firstId = (firstRow?.querySelector('td') as HTMLTableCellElement)?.textContent?.trim()

    const sortedAsc = [...ORDERS].sort((a, b) => a.customer.localeCompare(b.customer))
    expect(firstId).toBe(sortedAsc[0]!.id)
  })

  it('shows an empty state when a search matches no rows', () => {
    render(<App />)
    goto('Orders')

    const search = document.getElementById('q') as HTMLInputElement
    fireEvent.change(search, { target: { value: 'zzzz-no-such-order' } })

    expect(screen.getByText('No orders match your filters')).toBeInTheDocument()
  })
})

describe('Analytics page (US4)', () => {
  it('renders the channel table and charts', () => {
    render(<App />)
    goto('Analytics')

    expect(screen.getByText('Channel performance')).toBeInTheDocument()
    expect(screen.getByText('Organic search')).toBeInTheDocument()
    expect(screen.getByText('Acquisition funnel')).toBeInTheDocument()
    expect(document.getElementById('fun')).toBeInTheDocument()
    expect(document.getElementById('coh')).toBeInTheDocument()
  })
})

describe('Reports page (US4)', () => {
  it('lists saved reports and renders a preview for the selected report', () => {
    render(<App />)
    goto('Reports')

    expect(screen.getByText('Saved reports')).toBeInTheDocument()
    for (const r of SAVED_REPORTS) {
      expect(screen.getAllByText(r.name).length).toBeGreaterThanOrEqual(1)
    }
    expect(document.getElementById('repChart')).toBeInTheDocument()

    const second = SAVED_REPORTS[1]!
    fireEvent.click(screen.getAllByText(second.name)[0]!)
    expect(document.getElementById('repChart')).toBeInTheDocument()
  })
})

describe('ErrorBoundary (FR-009)', () => {
  function Bomb(): never {
    throw new Error('boom')
  }

  it('shows a clear error with a retry action on page failure', () => {
    const original = console.error
    console.error = () => {}

    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>,
    )

    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
    expect(screen.getByText(/boom/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()

    console.error = original
  })
})
