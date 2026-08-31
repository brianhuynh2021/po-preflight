import { useMemo, useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { Header } from './components/Header'
import { pageMeta, type PageKey } from './pages'
import { Dashboard } from './pages/Dashboard'
import { AnalyticsPage } from './pages/Analytics'
import { ReportsPage } from './pages/Reports'
import { CustomersPage, CUSTOMERS } from './pages/Customers'
import { OrdersPage, ORDERS } from './pages/Orders'
import { ProductsPage, PRODUCTS } from './pages/Products'
import { InvoicesPage, INVOICES } from './pages/Invoices'
import { SettingsPage } from './pages/Settings'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Page } from './components/Page'
import { Glow } from './components/Glow'
import { initTheme } from './lib/theme'

// Ensure theme is applied before first paint.
if (typeof document !== 'undefined') {
  initTheme()
}

export default function App() {
  const [page, setPage] = useState<PageKey>('dashboard')
  const [query, setQuery] = useState('')

  const header = useMemo(
    () =>
      pageMeta(page, {
        customers: CUSTOMERS.length,
        orders: ORDERS.length,
        products: PRODUCTS.length,
        invoices: INVOICES.length,
      }),
    [page],
  )

  const navigate = (p: PageKey, resetQuery = true) => {
    setPage(p)
    if (resetQuery) setQuery('')
  }

  const content = (() => {
    switch (page) {
      case 'dashboard':
        return <Dashboard />
      case 'analytics':
        return <AnalyticsPage />
      case 'reports':
        return <ReportsPage />
      case 'customers':
        return <CustomersPage query={query} />
      case 'orders':
        return <OrdersPage query={query} status="All" />
      case 'products':
        return <ProductsPage query={query} stock="All" />
      case 'invoices':
        return <InvoicesPage query={query} />
      case 'settings':
        return <SettingsPage />
    }
  })()

  return (
    <>
      <Glow />
      <div className="app">
        <Sidebar page={page} onNavigate={navigate} ordersBadge={12} />
        <main>
          <Header meta={header} onSearch={setQuery} />
          <div className="wrap" id="view">
            <ErrorBoundary key={page}>
              <Page>{content}</Page>
            </ErrorBoundary>
          </div>
        </main>
      </div>
    </>
  )
}
