import { useState } from 'react'
import { Panel } from '../components/Panel'
import { Seg } from '../components/Seg'
import { EChart } from '../lib/chart'
import { DataTable, type Column } from '../components/DataTable'
import { money } from '../lib/format'
import { cssVar } from '../lib/theme'
import { fmt } from '../lib/format'
import { CHANNELS, COHORT_DAYS, COHORT_ROWS, COHORT_WEEKS, FUNNEL, type Channel } from '../data/meta'

export function AnalyticsPage() {
  const [period, setPeriod] = useState<'30d' | '90d' | '12m'>('90d')
  const [page, setPage] = useState(1)

  const funnelData = FUNNEL.map(([name, value]) => ({
    name,
    value,
  }))

  const heatData: [number, number, number][] = []
  COHORT_ROWS.forEach((row, wi) => {
    row.forEach((v, di) => {
      heatData.push([di, wi, v])
    })
  })

  const channelCols: Column<Channel>[] = [
    { key: 'channel', label: 'Channel', sortable: true },
    { key: 'sessions', label: 'Sessions', sortable: true, numeric: true },
    { key: 'signups', label: 'Signups', sortable: true, numeric: true },
    { key: 'cvr', label: 'CVR', sortable: true, numeric: true, render: (c) => `${c.cvr}%` },
    { key: 'cac', label: 'CAC', sortable: true, numeric: true, render: (c) => (c.cac ? money(c.cac) : '—') },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className="g2">
        <Panel
          title="Acquisition funnel"
          tools={
            <Seg
              options={[
                { value: '30d', label: '30d' },
                { value: '90d', label: '90d' },
                { value: '12m', label: '12m' },
              ]}
              value={period}
              onChange={setPeriod}
            />
          }
        >
          <EChart
            id="fun"
            deps={[period]}
            build={() => ({
              tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (p: unknown) => {
                const arr = p as { name: string; value: number }[]
                const it = arr[0]!
                return `${it.name}<br/><b>${it.value.toLocaleString()}</b>`
              } },
              grid: { left: 88, right: 44, top: 8, bottom: 8 },
              xAxis: { type: 'value', show: false, max: (v: { max: number }) => v.max },
              yAxis: {
                type: 'category',
                data: [...funnelData].map((f) => f.name).reverse(),
                axisLabel: { color: cssVar('--muted'), fontSize: 11.5 },
                axisLine: { show: false },
                axisTick: { show: false },
              },
              series: [
                {
                  type: 'bar',
                  data: [...funnelData].map((f) => f.value).reverse(),
                  barWidth: 13,
                  itemStyle: { color: cssVar('--accent'), borderRadius: [0, 2, 2, 0] },
                  label: {
                    show: true,
                    position: 'right',
                    formatter: (p: any) => fmt(p.value),
                    color: cssVar('--muted'),
                    fontFamily: cssVar('--mono'),
                    fontSize: 11,
                  },
                },
              ],
            })}
          />
        </Panel>

        <Panel title="Weekly cohort retention">
          <EChart
            id="coh"
            build={() => ({
              tooltip: { position: 'top', formatter: (p: any) => {
                const [di, wi, v] = p.data as [number, number, number]
                return `${COHORT_WEEKS[wi]} · ${COHORT_DAYS[di]}: ${v}%`
              } },
              grid: { left: 40, right: 14, top: 22, bottom: 26 },
              xAxis: { type: 'category', data: COHORT_DAYS, splitArea: { show: false } },
              yAxis: { type: 'category', data: COHORT_WEEKS, splitLine: { show: false } },
              visualMap: {
                min: 30,
                max: 100,
                calculable: false,
                orient: 'horizontal',
                left: 'center',
                top: 0,
                inRange: { color: [cssVar('--bg'), cssVar('--accent-soft'), cssVar('--accent')] },
                show: false,
              },
              series: [
                {
                  type: 'heatmap',
                  data: heatData,
                  label: {
                    show: true,
                    formatter: (p: any) => (p.value[2] === 100 ? '' : `${p.value[2]}`),
                    color: ((p: any) => (p.value[2] > 78 ? cssVar('--accent-ink') : cssVar('--ink'))) as unknown as string,
                    fontFamily: cssVar('--mono'),
                    fontSize: 10,
                  },
                  itemStyle: { borderColor: cssVar('--panel'), borderWidth: 2, borderRadius: 2 },
                  emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.3)' } },
                },
              ],
            })}
          />
        </Panel>
      </div>

      <Panel title="Channel performance">
        <DataTable<Channel>
          columns={channelCols}
          rows={CHANNELS}
          rowKey={(c) => c.channel}
          page={page}
          onPage={setPage}
          pageSize={8}
        />
      </Panel>
    </div>
  )
}
