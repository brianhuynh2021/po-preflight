import * as echarts from 'echarts'
import { useEffect, useRef } from 'react'
import { cssVar, onThemeChange } from './theme'

// Builds ECharts base option scaffolding from the current design tokens so all
// charts match the reference look and re-theme when the app theme toggles.
export function baseOption(): echarts.EChartsOption {
  const font = cssVar('--sans', 'sans-serif')
  const mono = cssVar('--mono', 'monospace')
  const panel = cssVar('--panel', '#ffffff')
  const line = cssVar('--line', '#e8e3da')
  const lineSoft = cssVar('--line-soft', '#f2eee7')
  const ink = cssVar('--ink', '#14140f')
  const faint = cssVar('--faint', '#a09a90')
  const muted = cssVar('--muted', '#6d675f')
  const s1 = cssVar('--s1', '#1d4ed8')
  const s2 = cssVar('--s2', '#e08b3c')

  return {
    textStyle: { fontFamily: font, color: ink },
    color: [s1, s2],
    grid: { left: 10, right: 12, top: 24, bottom: 8, containLabel: true },
    tooltip: {
      backgroundColor: panel,
      borderColor: line,
      textStyle: { color: ink, fontFamily: font, fontSize: 12 },
      axisPointer: { lineStyle: { color: line } },
    },
    legend: {
      textStyle: { color: faint, fontFamily: font, fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10,
      icon: 'roundRect',
      top: 0,
      right: 0,
    },
    axisLine: { lineStyle: { color: line } },
    splitLine: { lineStyle: { color: lineSoft } },
    axisLabel: {
      color: faint,
      fontFamily: mono,
      fontSize: 10,
      fontFeatureSettings: 'tnum',
    },
    axisName: { color: muted },
  }
}

export interface EChartProps {
  id?: string
  build: () => echarts.EChartsOption
  deps?: readonly unknown[]
  className?: string
  style?: React.CSSProperties
}

let instanceSeq = 0

// A React wrapper around ECharts that mirrors the reference `as` component:
// create on mount, set option on deps change, re-theme and resize globally.
export function EChart({ id, build, deps = [], className = 'chart', style }: EChartProps) {
  const ref = useRef<HTMLDivElement>(null)
  const inst = useRef<echarts.ECharts | null>(null)
  const buildRef = useRef(build)
  buildRef.current = build
  const chartId = useRef(id || `chart-${++instanceSeq}`)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (!echarts.getInstanceByDom(el)) {
      inst.current = echarts.init(el, undefined, { renderer: 'canvas' })
    } else {
      inst.current = echarts.getInstanceByDom(el)!
    }
    inst.current!.setOption(buildRef.current(), true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
    return () => {
      inst.current?.dispose()
      inst.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    inst.current?.setOption(buildRef.current(), true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    const off = onThemeChange(() => {
      inst.current?.setOption(buildRef.current(), true)
    })
    const onResize = () => inst.current?.resize()
    window.addEventListener('resize', onResize)
    return () => {
      off()
      window.removeEventListener('resize', onResize)
    }
  }, [])

  return <div className={className} id={chartId.current} style={style} ref={ref} />
}
