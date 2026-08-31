// Toggle switch (reference .sw with role="switch").
export function Sw({
  on,
  onToggle,
  k,
}: {
  on: boolean
  onToggle: (next: boolean) => void
  k: string
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      data-k={k}
      className={`sw ${on ? 'on' : ''}`}
      onClick={() => onToggle(!on)}
    />
  )
}
