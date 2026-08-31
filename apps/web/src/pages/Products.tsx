import { useMemo, useState } from 'react'
import { Panel } from '../components/Panel'
import { Seg } from '../components/Seg'
import { money } from '../lib/format'
import { generateProducts } from '../data/products'

export const PRODUCTS = generateProducts()

type StockFilter = 'All' | 'Below reorder'

export function ProductsPage({ query, stock }: { query: string; stock: StockFilter }) {
  const [page, setPage] = useState(1)

  const rows = useMemo(() => {
    let r = PRODUCTS
    if (stock === 'Below reorder') r = r.filter((p) => p.stock < p.reorder)
    if (query) r = r.filter((p) => JSON.stringify(p).toLowerCase().includes(query.toLowerCase()))
    return r
  }, [stock, query])

  return (
    <Panel
      title="Products"
      tools={
        <>
          <Seg
            id="stockSeg"
            options={[
              { value: 'All', label: 'All' },
              { value: 'Below reorder', label: 'Below reorder' },
            ]}
            value={stock}
            onChange={() => setPage(1)}
          />
          <span className="faint" style={{ fontSize: 11.5 }}>
            {rows.length} shown
          </span>
        </>
      }
    >
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>SKU</th>
            <th className="n">Price</th>
            <th className="n">Sold 30d</th>
            <th style={{ width: '26%' }}>Stock vs reorder</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={5}>
                <div className="empty">No products match your filters</div>
              </td>
            </tr>
          ) : (
            rows
              .slice((page - 1) * 8, page * 8)
              .map((p) => {
                const low = p.stock < p.reorder
                const max = Math.max(p.reorder * 2, p.stock, 1)
                const pct = Math.min(100, (p.stock / max) * 100)
                const fill = low ? 'var(--warn)' : 'var(--accent)'
                return (
                  <tr key={p.sku}>
                    <td>
                      <span style={{ fontWeight: 520 }}>{p.name}</span>
                    </td>
                    <td className="faint">{p.sku}</td>
                    <td className="n num">{money(p.price)}</td>
                    <td className="n num">{p.sold}</td>
                    <td>
                      <div className="bar" style={{ margin: 0 }}>
                        <div className="r">
                          <b>{low ? `${p.stock} · below reorder` : `${p.stock} in stock`}</b>
                          <span className="dim">reorder {p.reorder}</span>
                        </div>
                        <div className="track">
                          <i style={{ width: `${pct}%`, background: fill }} />
                        </div>
                      </div>
                    </td>
                  </tr>
                )
              })
          )}
        </tbody>
      </table>
    </Panel>
  )
}
