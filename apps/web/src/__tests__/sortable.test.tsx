import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { caretDir, sortRows } from '../lib/sortable'
import { DataTable, type Column } from '../components/DataTable'

const rows = [
  { id: 'b', total: 300, name: 'Beta' },
  { id: 'c', total: 100, name: 'Charlie' },
  { id: 'a', total: 200, name: 'Alpha' },
]

type Row = (typeof rows)[number]

describe('sortRows', () => {
  it('sorts numerically ascending and descending', () => {
    expect(sortRows(rows, 'total', 'asc', 'n').map((r) => r.id)).toEqual(['c', 'a', 'b'])
    expect(sortRows(rows, 'total', 'desc', 'n').map((r) => r.id)).toEqual(['b', 'a', 'c'])
  })

  it('sorts alphabetically with localeCompare', () => {
    expect(sortRows(rows, 'name', 'asc', 's').map((r) => r.name)).toEqual(['Alpha', 'Beta', 'Charlie'])
    expect(sortRows(rows, 'name', 'desc', 's').map((r) => r.name)).toEqual(['Charlie', 'Beta', 'Alpha'])
  })
})

describe('caretDir', () => {
  it('returns the ascending/down caret glyph', () => {
    expect(caretDir('asc')).toBe('↑')
    expect(caretDir('desc')).toBe('↓')
  })
})

describe('DataTable sortable headers', () => {
  const columns: Column<Row>[] = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'total', label: 'Total', sortable: true, numeric: true },
  ]

  function rowTexts(): string[] {
    return screen.getAllByRole('row').slice(1).map((r) => r.textContent ?? '')
  }

  function setup() {
    return render(
      <DataTable
        columns={columns}
        rows={rows as Row[]}
        rowKey={(r: Row) => r.id}
        page={1}
        onPage={() => {}}
        pageSize={10}
      />,
    )
  }

  it('toggles a column ascending then descending with data-dir and caret', () => {
    setup()

    const nameHeader = screen.getByText('Name').closest('th') as HTMLTableCellElement
    const header = () => nameHeader

    // First click: ascending (alphabetical).
    fireEvent.click(screen.getByText('Name'))
    expect(header().getAttribute('data-dir')).toBe('asc')
    expect(header().getAttribute('aria-sort')).toBe('ascending')
    expect(header().querySelector('.caret')?.textContent).toBe('↑')
    expect(rowTexts()[0]).toContain('Alpha')

    // Second click: descending.
    fireEvent.click(screen.getByText('Name'))
    expect(header().getAttribute('data-dir')).toBe('desc')
    expect(header().getAttribute('aria-sort')).toBe('descending')
    expect(header().querySelector('.caret')?.textContent).toBe('↓')
    expect(rowTexts()[0]).toContain('Charlie')
  })

  it('sorts numerically by the Total column', () => {
    setup()

    fireEvent.click(screen.getByText('Total'))
    expect(rowTexts()[0]).toContain('100')
    expect(rowTexts()[0]).toContain('Charlie')

    fireEvent.click(screen.getByText('Total'))
    expect(rowTexts()[0]).toContain('300')
    expect(rowTexts()[0]).toContain('Beta')
  })
})
