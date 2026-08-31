import { useEffect, useRef, useState } from 'react'
import { EChart } from '../lib/chart'
import { cssVar } from '../lib/theme'
import { count, fmt, money } from '../lib/format'
import { type Kpi as KpiData, KPI_SPARKS, MONTHS } from '../data/meta'
import { Reveal } from './ui'

// KPI card with count-up value, delta, and ECharts sparkline.
export function Kpi({ kpi, index }: { kpi: KpiData; index: number }) {
  const [value, setValue] = useState(0)
  const targetRef = useRef(kpi.to)
  targetRef.current = kpi.to

  useEffect(() => {
    const cancel = count(targetRef.current, 900, setValue)
    return cancel
  }, [])

  const deltaGood = kpi.goodDown ? kpi.d <= 0 : kpi.d >= 0
  const formatted = kpi.money ? money(value) : kpi.pct ? `${value.toFixed(1)}%` : fmt(value)

  return (
    <Reveal as="div" className="kpi" index={index}>
      <div className="lbl">{kpi.lbl}</div>
      <div className="val">{formatted}</div>
      <span className={`delta ${deltaGood ? 'pos' : 'neg'}`}>
        {kpi.d >= 0 ? '↑' : '↓'} {Math.abs(kpi.d)}%
        <em> vs last month</em>
      </span>
      <div className="spark">
        <EChart
          id={`sp${index}`}
          build={() => ({
            animation: false,
            grid: { left: 0, right: 0, top: 0, bottom: 0 },
            xAxis: { type: 'category', show: false, data: MONTHS },
            yAxis: { type: 'value', show: false },
            series: [
              {
                type: 'line',
                data: KPI_SPARKS[index]!,
                symbol: 'none',
                smooth: true,
                lineStyle: { width: 1.5, color: cssVar('--accent', '#ff7a1a') },
                areaStyle: { color: cssVar('--accent', '#ff7a1a'), opacity: 0.08 },
              },
            ],
          })}
          className="spark"
        />
      </div>
    </Reveal>
  )
}
