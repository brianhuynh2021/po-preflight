import '@testing-library/jest-dom/vitest'
import { vi } from 'vitest'
import type { ECharts, EChartsOption } from 'echarts'

// jsdom cannot render the ECharts canvas, so stub the canvas instance methods
// used by the EChart wrapper (lib/chart.tsx). Charts mount a div with the given
// id so tests can assert presence.
function makeStub(id: string) {
  const stub = {
    id,
    setOption: vi.fn((_o: EChartsOption, _notMerge?: boolean) => {}),
    resize: vi.fn(),
    dispose: vi.fn(),
    getDom: () => null,
  } as unknown as ECharts
  return stub
}

vi.mock('echarts', () => {
  const instances = new Map<string, ECharts>()
  let seq = 0
  return {
    init: (el: HTMLElement) => {
      const id = el.id || `chart-${++seq}`
      const stub = makeStub(id)
      instances.set(id, stub)
      return stub
    },
    getInstanceByDom: (el: HTMLElement) =>
      (el && instances.get(el.id)) || null,
    dispose: (el: HTMLElement) => {
      if (el) instances.delete(el.id)
    },
  }
})

// jsdom lacks a 2D canvas context; WorldMap guards `getContext('2d') === null`.
// Patch the prototype to return null silently instead of emitting jsdom's
// "Not implemented" stderr noise during tests.
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  configurable: true,
  writable: true,
  value: () => null,
})
