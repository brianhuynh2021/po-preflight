// Sort utilities for data tables.

export type SortDir = 'asc' | 'desc'
export type SortType = 's' | 'n'

export interface SortState {
  key: string
  dir: SortDir
  type: SortType
}

// Numeric extraction mirrors the reference's "strip non-digits" behavior.
function numericValue(value: unknown): number {
  const num = Number(value)
  if (Number.isFinite(num)) return num
  if (typeof value === 'string') {
    const digits = Number(value.replace(/[^\d.-]/g, ''))
    return Number.isFinite(digits) ? digits : 0
  }
  return 0
}

function cellValue(row: Record<string, unknown>, key: string): unknown {
  return row[key]
}

// Returns rows sorted ascending per `type`; caller flips `dir` for descending.
export function sortRows(
  rows: Record<string, unknown>[],
  key: string,
  dir: SortDir,
  type: SortType,
): Record<string, unknown>[] {
  const dirFactor = dir === 'asc' ? 1 : -1
  const sorted = [...rows].sort((a, b) => {
    const av = cellValue(a, key)
    const bv = cellValue(b, key)
    const cmp =
      type === 'n' ? numericValue(av) - numericValue(bv) : String(av ?? '').localeCompare(String(bv ?? ''))
    // Deterministic position for null/undefined (treat as smallest).
    const aMissing = av === null || av === undefined
    const bMissing = bv === null || bv === undefined
    if (aMissing && bMissing) return 0
    if (aMissing) return dir === 'asc' ? -1 : 1
    if (bMissing) return dir === 'asc' ? 1 : -1
    return cmp * dirFactor
  })
  return sorted
}

// Header caret text shown for the active sort column.
export function caretDir(dir: SortDir): string {
  return dir === 'asc' ? '↑' : '↓'
}
