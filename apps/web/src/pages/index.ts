import { type HeaderMeta } from '../components/Header'

export type PageKey =
  | 'dashboard'
  | 'analytics'
  | 'reports'
  | 'customers'
  | 'orders'
  | 'products'
  | 'invoices'
  | 'settings'

export const PAGE_KEYS: PageKey[] = [
  'dashboard',
  'analytics',
  'reports',
  'customers',
  'orders',
  'products',
  'invoices',
  'settings',
]

export const PAGE_TITLES: Record<PageKey, string> = {
  dashboard: 'Dashboard',
  analytics: 'Analytics',
  reports: 'Reports',
  customers: 'Customers',
  orders: 'Orders',
  products: 'Products',
  invoices: 'Invoices',
  settings: 'Settings',
}

export function pageMeta(
  page: PageKey,
  counts: { customers: number; orders: number; products: number; invoices: number },
): HeaderMeta {
  switch (page) {
    case 'dashboard':
      return { title: 'Dashboard', crumb: 'Last updated 4 minutes ago' }
    case 'analytics':
      return { title: 'Analytics', crumb: 'Acquisition and retention · last 90 days' }
    case 'reports':
      return { title: 'Reports', crumb: '6 saved reports · 2 scheduled' }
    case 'customers':
      return { title: 'Customers', crumb: `${counts.customers} accounts` }
    case 'orders':
      return { title: 'Orders', crumb: `${counts.orders} orders in the last 20 days` }
    case 'products':
      return { title: 'Products', crumb: `${counts.products} active SKUs` }
    case 'invoices':
      return { title: 'Invoices', crumb: `${counts.invoices} invoices · aging by days outstanding` }
    case 'settings':
      return { title: 'Settings', crumb: 'Workspace preferences' }
  }
}
