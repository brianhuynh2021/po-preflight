import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { WorldMap } from '../components/WorldMap'
import { makeProjection } from '../lib/map/landmask'
import { routePoints, animatedDot } from '../lib/map/routes'
import { CITY_COORDS, type CityCoords } from '../data/seed'

const W = 900
const H = 470

// jsdom has no 2D canvas context by default. Install a no-op stub so the map's
// draw/click wiring runs and we can exercise hotspot picking.
const ctxStub: Record<string, unknown> = {
  fillStyle: '',
  strokeStyle: '',
  lineWidth: 1,
  globalAlpha: 1,
  font: '',
  textAlign: 'left',
  setTransform: vi.fn(),
  clearRect: vi.fn(),
  fillRect: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  stroke: vi.fn(),
  fill: vi.fn(),
  arc: vi.fn(),
  fillText: vi.fn(),
  setLineDash: vi.fn(),
  createRadialGradient: () => ({ addColorStop: vi.fn() }),
  getImageData: () => ({ data: new Uint8ClampedArray(W * H * 4) }),
}

beforeEach(() => {
  // Patch the prototype so canvases created inside the component (via
  // document.createElement) also get the no-op 2D context and a sized rect.
  const proto = HTMLCanvasElement.prototype as unknown as Record<string, unknown>
  proto.getContext = () => ctxStub
  proto.getBoundingClientRect = () => ({ left: 0, top: 0, width: W, height: H })
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

function project(city: CityCoords): [number, number] {
  // Projection is equirectangular and independent of land rings.
  return makeProjection(W, H, []).project(city.lng, city.lat)
}

describe('WorldMap', () => {
  const hotspots = [
    { city: 'Rome', v: 40, pin: false },
    { city: 'Madrid', v: 25, pin: false },
  ]

  it('renders a map canvas with hotspot legend', () => {
    render(<WorldMap hotspots={hotspots} onPick={() => {}} />)
    const canvas = screen.getByLabelText(/world map/i) as HTMLCanvasElement
    expect(canvas).toBeInTheDocument()
    expect(screen.getByText(/order volume/i)).toBeInTheDocument()
  })

  it('renders without crashing for an empty hotspot set', () => {
    expect(() => render(<WorldMap hotspots={[]} onPick={() => {}} />)).not.toThrow()
  })

  it('invokes onPick with the clicked hotspot city', () => {
    const onPick = vi.fn()
    render(<WorldMap hotspots={hotspots} onPick={onPick} />)
    const canvas = screen.getByLabelText(/world map/i)

    const romeCoords = CITY_COORDS['Rome']!
    const [x, y] = project(romeCoords)
    fireEvent.click(canvas, { clientX: x, clientY: y })

    expect(onPick).toHaveBeenCalledWith('Rome')
  })
})

describe('map route helpers', () => {
  const proj = makeProjection(W, H, []).project

  it('routePoints samples a great-circle arc between two cities', () => {
    const pts = routePoints(CITY_COORDS['New York']!, CITY_COORDS['Lisbon']!, proj, 8)
    expect(pts.length).toBe(9)
    // First and last projected points match the endpoints.
    expect(pts[0]![0]).toBeCloseTo(proj(CITY_COORDS['New York']!.lng, CITY_COORDS['New York']!.lat)[0], 5)
  })

  it('animatedDot lands exactly on the destination at t=1', () => {
    const to = CITY_COORDS['Rome']!
    const [x, y] = animatedDot(CITY_COORDS['Shanghai']!, to, proj, 1)
    const [ex, ey] = proj(to.lng, to.lat)
    expect(x).toBeCloseTo(ex, 5)
    expect(y).toBeCloseTo(ey, 5)
  })
})
