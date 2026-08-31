import type { PageKey } from '../pages'

interface NavGroup {
  label: string
  items: { key: PageKey; label: string }[]
}

const NAV: NavGroup[] = [
  {
    label: 'Overview',
    items: [
      { key: 'dashboard', label: 'Dashboard' },
      { key: 'analytics', label: 'Analytics' },
      { key: 'reports', label: 'Reports' },
    ],
  },
  {
    label: 'Manage',
    items: [
      { key: 'customers', label: 'Customers' },
      { key: 'orders', label: 'Orders' },
      { key: 'products', label: 'Products' },
      { key: 'invoices', label: 'Invoices' },
    ],
  },
  { label: 'System', items: [{ key: 'settings', label: 'Settings' }] },
]

function Icon({ name }: { name: string }) {
  const paths: Record<string, React.ReactNode> = {
    dashboard: (
      <>
        <rect x="3" y="3" width="7" height="9" rx="1.5" />
        <rect x="14" y="3" width="7" height="5" rx="1.5" />
        <rect x="14" y="12" width="7" height="9" rx="1.5" />
        <rect x="3" y="16" width="7" height="5" rx="1.5" />
      </>
    ),
    analytics: (
      <>
        <path d="M4 20V10" />
        <path d="M10 20V4" />
        <path d="M16 20v-8" />
        <path d="M22 20H2" />
      </>
    ),
    reports: (
      <>
        <path d="M7 3h7l6 6v12H7z" />
        <path d="M14 3v6h6" />
        <path d="M10 14h6M10 18h6" />
      </>
    ),
    customers: (
      <>
        <circle cx="9" cy="8" r="3.2" />
        <path d="M3 20c0-3.2 2.7-5 6-5s6 1.8 6 5" />
        <circle cx="17" cy="9" r="2.4" />
        <path d="M18.6 17.4c.9.5 1.4 1.3 1.4 2.6" />
      </>
    ),
    orders: (
      <>
        <path d="M6 3h12l2 5v13H4V8z" />
        <path d="M4 8h16" />
        <path d="M8 12h8" />
      </>
    ),
    products: (
      <>
        <path d="M12 3 4 7v10l8 4 8-4V7z" />
        <path d="M4 7l8 4 8-4" />
        <path d="M12 11v10" />
      </>
    ),
    invoices: (
      <>
        <path d="M6 3h9l3.5 3.5V21H6z" />
        <path d="M15 3v3.5h3.5" />
        <path d="M9 12h6M9 16h4" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" />
      </>
    ),
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {paths[name]}
    </svg>
  )
}

export function Sidebar({ page, onNavigate, ordersBadge }: { page: PageKey; onNavigate: (p: PageKey) => void; ordersBadge?: number }) {
  return (
    <aside>
      <div className="brand">
        <svg className="logo" viewBox="0 0 24 24" aria-hidden="true">
          <rect className="s" x="2.5" y="2.5" width="19" height="19" rx="5" />
          <path className="n" d="M7 16V8h3l3 5 3-5h3v8h-2v-5l-2.5 4H12L9.5 11v5z" />
          <circle className="ring" cx="19" cy="5" r="2.2" />
          <path className="tick" d="M18 5l.7.7L19.6 4.6" />
        </svg>
        Northwind
      </div>
      <nav id="nav">
        {NAV.map((group) => (
          <div key={group.label}>
            <div className="navlabel">{group.label}</div>
            {group.items.map((item) => (
              <button
                key={item.key}
                type="button"
                className={`navitem ${page === item.key ? 'on' : ''}`}
                onClick={() => onNavigate(item.key)}
              >
                <Icon name={item.key} />
                {item.label}
                {item.key === 'orders' && ordersBadge != null && ordersBadge > 0 && (
                  <span className="badge" id="navOrders">
                    {ordersBadge}
                  </span>
                )}
              </button>
            ))}
          </div>
        ))}
      </nav>
      <div className="who">
        <div className="av">AR</div>
        <div>
          <div style={{ fontSize: 12.5, fontWeight: 520 }}>Ana Reyes</div>
          <div className="faint" style={{ fontSize: 11 }}>
            Operations lead
          </div>
        </div>
      </div>
    </aside>
  )
}
