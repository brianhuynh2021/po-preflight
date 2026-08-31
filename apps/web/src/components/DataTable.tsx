import { useMemo, useState } from 'react'
import { caretDir, sortRows, type SortDir, type SortState, type SortType } from '../lib/sortable'

export interface Column<T extends object = Record<string, unknown>> {
  key: string
  label: React.ReactNode
  sortable?: boolean
  numeric?: boolean
  render?: (row: T, value: unknown, rowIndex: number) => React.ReactNode
}

interface DataTableProps<T extends object> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T, i: number) => string
  empty?: React.ReactNode
  pageSize?: number
  // Default sort applied initially (key + type).
  defaultSort?: { key: string; type: SortType; dir?: SortDir }
  // When page/onPage are omitted the full dataset is rendered without a footer.
  page?: number
  onPage?: (page: number) => void
  onSort?: (s: SortState | null) => void
  sort?: SortState | null
  showFooter?: boolean
}

// Sortable, paginated data table with an empty state.
export function DataTable<T extends object>({
  columns,
  rows,
  rowKey,
  empty = 'No records found',
  pageSize = 8,
  defaultSort,
  page,
  onPage,
  onSort,
  sort:   externalSort,
  showFooter: _showFooter = true,
}: DataTableProps<T>) {
  const [internalSort, setInternalSort] = useState<SortState | null>(() =>
    defaultSort ? { key: defaultSort.key, dir: defaultSort.dir ?? 'asc', type: defaultSort.type } : null,
  )
  const sort = externalSort !== undefined ? externalSort : internalSort

  const sorted = useMemo(() => {
    if (!sort) return [...rows]
    return sortRows(rows as unknown as Record<string, unknown>[], sort.key, sort.dir, sort.type) as T[]
  }, [rows, sort])

  const totalPages = page !== undefined ? Math.max(1, Math.ceil(sorted.length / pageSize)) : 1
  const pageIndex = page !== undefined ? Math.min(page, totalPages) : 1
  const current = page !== undefined ? sorted.slice((pageIndex - 1) * pageSize, pageIndex * pageSize) : sorted

  const toggleSort = (col: Column<T>) => {
    if (!col.sortable) return
    const type: SortType = col.numeric ? 'n' : 's'
    let next: SortState | null
    if (!sort || sort.key !== col.key) next = { key: col.key, dir: 'asc', type }
    else if (sort.dir === 'asc') next = { key: col.key, dir: 'desc', type }
    else next = null
    setInternalSort(next)
    onSort?.(next)
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`${col.sortable ? 'sortable' : ''} ${col.numeric ? 'n' : ''}`}
                data-sort={col.sortable ? (col.numeric ? 'n' : 's') : undefined}
                data-dir={sort?.key === col.key ? sort.dir : undefined}
                onClick={() => toggleSort(col)}
                aria-sort={sort?.key === col.key ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                {col.label}
                {sort?.key === col.key && <span className="caret">{caretDir(sort.dir)}</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {current.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>
                <div className="empty">{empty}</div>
              </td>
            </tr>
          ) : (
            current.map((row, i) => (
              <tr key={rowKey(row, i)}>
                {columns.map((col) => (
                  <td key={col.key} className={col.numeric ? 'n' : ''}>
                    {col.render
                      ? col.render(row, (row as Record<string, unknown>)[col.key], i)
                      : ((row as Record<string, unknown>)[col.key] as React.ReactNode)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
      {page !== undefined && (
        <div className="tfoot">
          <span id="pgInfo">
            {sorted.length === 0
              ? `0–0 of 0`
              : `${(pageIndex - 1) * pageSize + 1}–${Math.min(pageIndex * pageSize, sorted.length)} of ${sorted.length}`}
          </span>
          <span className="pg" id="pg">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
              <button key={n} type="button" className={n === pageIndex ? 'on' : ''} onClick={() => onPage?.(n)}>
                {n}
              </button>
            ))}
          </span>
        </div>
      )}
    </div>
  )
}
