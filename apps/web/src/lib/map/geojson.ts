// Minimal TopoJSON decoder: converts a Topology's `land` geometry into planar
// [x, y] rings using the topology transform (equirectangular, in degrees).

// TopoJSON topology with transform.
export interface Topology {
  type: 'Topology'
  arcs: (number[] | number[][])[]
  transform: { scale: [number, number]; translate: [number, number] }
  objects: Record<string, { type: string; arcs?: unknown }>
}

export function decodeArcs(topology: Topology, arcIndices: number[]): [number, number][][] {
  return arcIndices.map((idx) => {
    const arc = topology.arcs[Math.abs(idx)] as number[]
    // arc is a flat array [x0,y0,x1,y1,...] of deltas, possibly reversed.
    const step = 2
    const xs: number[] = []
    const ys: number[] = []
    let px = 0
    let py = 0
    for (let i = 0; i * step < arc.length; i++) {
      px += arc[i * step] as number
      py += arc[i * step + 1] as number
      xs.push(px)
      ys.push(py)
    }
    if (idx < 0) {
      xs.reverse()
      ys.reverse()
    }
    const pts: [number, number][] = []
    for (let i = 0; i < xs.length; i++) {
      pts.push([xs[i]!, ys[i]!])
    }
    return pts
  })
}

// Convert encoded delta coordinates into [lng, lat] using the topology transform.
function toGeo(topology: Topology, ring: [number, number][]): [number, number][] {
  const { scale, translate } = topology.transform
  return ring.map(([x, y]) => [x * scale[0] + translate[0], y * scale[1] + translate[1]])
}

export interface Ring {
  points: [number, number][]
}

// Decode the `land` geometry into a list of lng/lat rings.
export function decodeLand(topology: Topology): Ring[] {
  const land = topology.objects['land'] as { type: string; arcs?: unknown }
  const rings: Ring[] = []
  const arcs = Array.isArray(land.arcs) ? (land.arcs as unknown[]) : []
  const collect = (items: unknown[]) => {
    for (const it of items) {
      // `it` is either a ring of arc indices (number[]) or a nested polygon
      // ring of arc indices (number[][]), where a polygon may contain holes.
      if (Array.isArray(it) && Array.isArray(it[0])) {
        collect(it as unknown[])
      } else if (Array.isArray(it) && typeof it[0] === 'number') {
        const decoded = decodeArcs(topology, it as number[])[0] ?? []
        const geo = toGeo(topology, decoded)
        rings.push({ points: geo })
      }
    }
  }
  collect(arcs)
  return rings
}

export async function loadLand(url = '/land-110m.json'): Promise<Topology> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Failed to load land topology: ${res.status}`)
  return (await res.json()) as Topology
}
