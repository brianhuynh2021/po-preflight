import { useEffect, useRef, useState } from 'react'
import { NOTIFICATIONS } from '../data/meta'
import { getTheme, toggleTheme } from '../lib/theme'

export interface HeaderMeta {
  title: string
  crumb: string
}

export function Header({
  meta,
  onSearch,
}: {
  meta: HeaderMeta
  onSearch: (q: string) => void
}) {
  const [unread] = useState(() => NOTIFICATIONS.filter((n) => n.read !== true).length)
  const [open, setOpen] = useState(false)
  const popRef = useRef<HTMLDivElement>(null)
  const [theme, setTheme] = useState(getTheme())

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (popRef.current && !popRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [])

  return (
    <header>
      <div style={{ minWidth: 0 }}>
        <h1 id="title">{meta.title}</h1>
        <div className="crumb" id="crumb">
          {meta.crumb}
        </div>
      </div>
      <div className="spacer" style={{ flex: 1 }} />
      <div className="search">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.3-4.3" />
        </svg>
        <input id="q" type="search" placeholder="Search orders, customers…" onChange={(e) => onSearch(e.target.value)} />
      </div>
      <button
        type="button"
        className="iconbtn"
        id="theme"
        title="Toggle theme"
        onClick={() => setTheme(toggleTheme())}
        aria-label="Toggle theme"
      >
        {theme === 'dark' ? <MoonIcon /> : <SunIcon />}
      </button>
      <button type="button" className="iconbtn" id="bell" aria-label="Notifications" onClick={() => setOpen((v) => !v)}>
        <BellIcon />
        {unread > 0 && <span className="dot" />}
      </button>
      <div className={`pop ${open ? 'on' : ''}`} id="pop" ref={popRef}>
        <div className="ph">Notifications · {unread} unread</div>
        {NOTIFICATIONS.map((n, i) => (
          <div className="pi" key={i}>
            <span className="d" style={{ background: `var(--${n.tone})` }} />
            <div>
              <div className="t">{n.title}</div>
              <div className="m">{n.detail}</div>
            </div>
            <span style={{ marginLeft: 'auto', color: 'var(--faint)', fontSize: 11, fontFamily: 'var(--mono)' }}>
              {n.time}
            </span>
          </div>
        ))}
      </div>
    </header>
  )
}

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 9a6 6 0 0 1 12 0c0 5 2 7 2 7H4s2-2 2-7" />
      <path d="M10 20a2 2 0 0 0 4 0" />
    </svg>
  )
}
function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z" />
    </svg>
  )
}
function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
    </svg>
  )
}
