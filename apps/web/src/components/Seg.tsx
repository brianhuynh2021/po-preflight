import { useEffect, useRef } from 'react'

export interface SegOption<T extends string = string> {
  value: T
  label: React.ReactNode
}

// Segmented control with a sliding pill indicator (reference .seg).
export function Seg<T extends string>({
  options,
  value,
  onChange,
  id,
}: {
  options: readonly SegOption<T>[]
  value: T
  onChange: (value: T) => void
  id?: string
}) {
  const wrapRef = useRef<HTMLSpanElement>(null)
  const index = options.findIndex((o) => o.value === value)

  useEffect(() => {
    const wrap = wrapRef.current
    if (!wrap) return
    const on = wrap.querySelector<HTMLElement>('[data-seg-on]')
    const pill = wrap.querySelector<HTMLElement>('.pill')
    if (!on || !pill) return
    pill.style.width = `${on.offsetWidth}px`
    pill.style.transform = `translateX(${on.offsetLeft - 2}px)`
  }, [index, options])

  return (
    <span className="seg" id={id} ref={wrapRef}>
      <span className="pill" aria-hidden="true" />
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          data-seg-on={o.value === value ? '' : undefined}
          data-v={o.value}
          className={o.value === value ? 'on' : ''}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </span>
  )
}
