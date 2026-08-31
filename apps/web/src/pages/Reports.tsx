import { useState } from 'react'
import { Panel } from '../components/Panel'
import { EChart } from '../lib/chart'
import { MONTHS, SAVED_REPORTS } from '../data/meta'
import { mulberry32 } from '../lib/rng'
import { cssVar } from '../lib/theme'
import { toast } from '../components/ui'

function reportSeries(index: number): number[] {
  const rand = mulberry32(9e3 + index)
  return Array.from({ length: 12 }, () => Math.round(1e3 + rand() * 9e3))
}

function exportCsv(name: string, series: number[]) {
  const csv = ['month,value', ...series.map((v, i) => `${i + 1},${v}`)].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${name}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export function ReportsPage() {
  const [index, setIndex] = useState(0)
  const active = SAVED_REPORTS[index]!

  return (
    <div className="g2">
      <Panel title="Saved reports">
        <div className="form">
          {SAVED_REPORTS.map((r, i) => (
            <div className="frow" key={r.slug}>
              <div className="fl">
                <div className="t">{r.name}</div>
                <div className="h">{r.schedule}</div>
              </div>
              <button type="button" className="btn" onClick={() => setIndex(i)}>
                Preview
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => {
                  exportCsv(r.slug, reportSeries(i))
                  toast(`Exported ${r.slug}.csv`)
                }}
              >
                Export CSV
              </button>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title={<span id="repName">{active.name}</span>}>
        <EChart
          id="repChart"
          className="chart fill"
          deps={[index]}
          build={() => ({
            tooltip: { trigger: 'axis' },
            grid: { left: 44, right: 12, top: 16, bottom: 22 },
            xAxis: { type: 'category', data: MONTHS },
            yAxis: { type: 'value', splitLine: { show: false } },
            series: [
              {
                type: 'bar',
                data: reportSeries(index),
                barWidth: '48%',
                itemStyle: { color: cssVar('--accent'), borderRadius: [2, 2, 0, 0] },
              },
            ],
          })}
        />
      </Panel>
    </div>
  )
}
