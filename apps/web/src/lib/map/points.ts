// Dot-cloud sampling of land into a set of drawable points for the map.

import { type Projection } from './landmask'

export interface Dot {
  x: number
  y: number
}

// Sample a dot cloud of land points across a regular lat/lng grid so the map
// renders continents as a scatter of dots (reference default step 1.6°).
export function sampleLandPoints(
  proj: Projection,
  stepDeg = 1.6,
  latMax = 83,
  latMin = -56,
): Dot[] {
  const dots: Dot[] = []
  for (let lat = latMax; lat >= latMin; lat -= stepDeg) {
    for (let lng = -180; lng <= 180; lng += stepDeg) {
      if (!proj.contains(lng, lat)) continue
      const [x, y] = proj.project(lng, lat)
      dots.push({ x, y })
    }
  }
  return dots
}
