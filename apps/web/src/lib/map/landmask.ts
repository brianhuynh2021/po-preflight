import { type Ring } from './geojson'

// Builds a projection + land hit-test from decoded land rings using an
// offscreen canvas. Falls back to a simple point-in-polygon test when no 2d
// context is available (e.g. jsdom in tests).

export interface Projection {
  // Map [lng, lat] in degrees to [x, y] in [0, width] x [0, height].
  project: (lng: number, lat: number) => [number, number]
  contains: (lng: number, lat: number) => boolean
}

export const EXTENT = {
  west: -180,
  east: 180,
  south: -85.6,
  north: 83.0,
}

function pointInPolygon(lng: number, lat: number, ring: [number, number][]): boolean {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i]![0]
    const yi = ring[i]![1]
    const xj = ring[j]![0]
    const yj = ring[j]![1]
    const intersect =
      yi > lat !== yj > lat && lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi
    if (intersect) inside = !inside
  }
  return inside
}

export function makeProjection(width: number, height: number, rings: Ring[]): Projection {
  const w = width
  const h = height

  const canvas =
    typeof document !== 'undefined'
      ? document.createElement('canvas')
      : null
  let maskCtx: CanvasRenderingContext2D | null = null
  if (canvas && canvas.getContext) {
    canvas.width = w
    canvas.height = h
    maskCtx = canvas.getContext('2d')
  }

  if (maskCtx) {
    // Rasterize land onto the mask canvas.
    maskCtx.fillStyle = '#000'
    maskCtx.fillRect(0, 0, w, h)
    maskCtx.fillStyle = '#fff'
    for (const ring of rings) {
      if (ring.points.length < 3) continue
      maskCtx.beginPath()
      ring.points.forEach(([lng, lat], i) => {
        const [x, y] = projectPoint(w, h, lng, lat)
        if (i === 0) maskCtx.moveTo(x, y)
        else maskCtx.lineTo(x, y)
      })
      maskCtx.closePath()
      maskCtx.fill('evenodd')
    }
    const imageData = maskCtx.getImageData(0, 0, w, h)
    const data = imageData.data
    const contains = (lng: number, lat: number): boolean => {
      const [x, y] = projectPoint(w, h, lng, lat)
      const i = (Math.round(y) * w + Math.round(x)) * 4
      if (i < 0 || i >= data.length) return false
      return data[i]! > 127
    }
    return { project: (lng, lat) => projectPoint(w, h, lng, lat), contains }
  }

  // Fallback: geometric point-in-polygon across rings (slow but works without canvas).
  const contains = (lng: number, lat: number): boolean =>
    rings.some((ring) => pointInPolygon(lng, lat, ring.points))
  return { project: (lng, lat) => projectPoint(w, h, lng, lat), contains }
}

function projectPoint(w: number, h: number, lng: number, lat: number): [number, number] {
  const x = ((lng - EXTENT.west) / (EXTENT.east - EXTENT.west)) * w
  const y = ((EXTENT.north - lat) / (EXTENT.north - EXTENT.south)) * h
  return [x, y]
}
