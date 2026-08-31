// Great-circle route arcs and animated-dot interpolation for the map.

import type { CityCoords } from '../../data/seed'
import type { Projection } from './landmask'

// Interpolate a lng/lat point at fraction t (0..1) along the great-circle
// path between two city coordinates. Used to draw route arcs and move dots.
export function greatCircle(
  from: CityCoords,
  to: CityCoords,
  t: number,
): [number, number] {
  const rad = Math.PI / 180
  const f1 = from.lat * rad
  const f2 = to.lat * rad
  const dl = (to.lng - from.lng) * rad
  const s = Math.sin(f1) * Math.sin(f2) + Math.cos(f1) * Math.cos(f2) * Math.cos(dl)
  const angle = Math.acos(Math.min(1, Math.max(-1, s)))
  if (angle < 1e-6) return [from.lng, from.lat]
  const sa = Math.sin(angle)
  const A = Math.sin((1 - t) * angle) / sa
  const B = Math.sin(t * angle) / sa
  const x = A * Math.cos(f1) * Math.cos(from.lng * rad) + B * Math.cos(f2) * Math.cos(to.lng * rad)
  const y = A * Math.cos(f1) * Math.sin(from.lng * rad) + B * Math.cos(f2) * Math.sin(to.lng * rad)
  const z = A * Math.sin(f1) + B * Math.sin(f2)
  const lat = Math.atan2(z, Math.hypot(x, y)) / rad
  const lng = Math.atan2(y, x) / rad
  return [lng, lat]
}

// Sample a great-circle arc as projected 2D points for stroking on the map.
export function routePoints(
  from: CityCoords,
  to: CityCoords,
  project: Projection['project'],
  steps = 48,
): [number, number][] {
  const pts: [number, number][] = []
  for (let i = 0; i <= steps; i++) {
    const [lng, lat] = greatCircle(from, to, i / steps)
    pts.push(project(lng, lat))
  }
  return pts
}

// Animated dot position (projected) at a phase in [0, 1) along a route.
export function animatedDot(
  from: CityCoords,
  to: CityCoords,
  project: Projection['project'],
  t: number,
): [number, number] {
  const [lng, lat] = greatCircle(from, to, t)
  return project(lng, lat)
}
