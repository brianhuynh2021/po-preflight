// Number / money formatting helpers (mirrors the reference `Zh` and friends).

const groupSep = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })

export function fmt(n: number): string {
  return groupSep.format(Math.round(n))
}

export function money(n: number): string {
  return '$' + fmt(n)
}

// Count-up animation from a start value to a target value over a duration (ms).
// Calls onTick with the current integer value each frame and onDone when complete.
export function count(
  to: number,
  duration = 900,
  onTick: (v: number) => void,
  onDone?: () => void,
): () => void {
  const start = performance.now()
  let raf = 0
  const step = (now: number) => {
    const t = Math.min(1, (now - start) / duration)
    const eased = 1 - Math.pow(1 - t, 3)
    onTick(Math.round(to * eased))
    if (t < 1) {
      raf = requestAnimationFrame(step)
    } else {
      onTick(to)
      onDone?.()
    }
  }
  raf = requestAnimationFrame(step)
  return () => cancelAnimationFrame(raf)
}
