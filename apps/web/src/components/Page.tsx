import type { ReactNode } from 'react'

// Page layout wrapper: a full-width vertical stack with a consistent gap,
// used to mount each of the eight console pages inside the app shell.
export function Page({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`page ${className}`} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {children}
    </div>
  )
}
