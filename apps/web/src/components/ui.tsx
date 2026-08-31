import { useLayoutEffect, useRef } from 'react'
import type { Tone } from '../data/meta'

// Simple stateless primers matching the reference look.

export function Tag({ children, tone = 'dim' }: { children: React.ReactNode; tone?: Tone | 'dim' }) {
  return <span className={`tag ${tone === 'dim' ? 'dim' : tone}`}>{children}</span>
}

export function Status({ children, tone = 'warn' }: { children: React.ReactNode; tone?: Tone }) {
  return <span className={`status ${tone}`}>{children}</span>
}

// Reveal-on-scroll wrapper (reference [data-reveal] animation).
export function Reveal({
  children,
  index = 0,
  as: As = 'div',
  className = '',
}: {
  children: React.ReactNode
  index?: number
  as?: React.ElementType
  className?: string
}) {
  const ref = useRef<HTMLElement | null>(null)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    el.classList.add('in')
    return () => el.classList.remove('in')
  }, [])

  return (
    <As ref={ref} className={className} data-reveal style={{ ['--i' as string]: index } as React.CSSProperties}>
      {children}
    </As>
  )
}

// Simple toast helper.
export function toast(msg: string): void {
  let host = document.querySelector<HTMLDivElement>('.kit-toasts')
  if (!host) {
    host = document.createElement('div')
    host.className = 'kit-toasts'
    document.body.appendChild(host)
  }
  const el = document.createElement('div')
  el.className = 'kit-toast'
  el.textContent = msg
  host.appendChild(el)
  setTimeout(() => el.remove(), 2600)
}
