import { useEffect, useRef } from 'react'
import { decodeLand, loadLand } from '../lib/map/geojson'
import { makeProjection } from '../lib/map/landmask'
import { sampleLandPoints, type Dot } from '../lib/map/points'
import { animatedDot, routePoints } from '../lib/map/routes'
import { CITY_COORDS, ROUTES } from '../data/seed'
import type { Hotspot } from '../data/orders'
import { cssVar, onThemeChange } from '../lib/theme'

interface WorldMapProps {
  hotspots: Hotspot[]
  pin?: string
  onPick: (city: string | null) => void
}

const W = 900
const H = 470

// Animated dot on a route: parametrize t in [0,1] along a great-circle segment.
let animFrame = 0

export function WorldMap({ hotspots, pin, onPick }: WorldMapProps) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const state = useRef({ hotspots, pin })
  state.current = { hotspots, pin }

  useEffect(() => {
    const wrap = wrapRef.current
    const canvas = canvasRef.current
    if (!wrap || !canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return // jsdom / no-2d fallback: nothing to draw

    let destroyed = false
    let landDots: Dot[] = []
    let landProj = makeProjection(W, H, [])
    let ready = false

    loadLand()
      .then((topo) => {
        if (destroyed) return
        const rings = decodeLand(topo)
        landProj = makeProjection(W, H, rings)
        landDots = sampleLandPoints(landProj, 1.6, 83, -56)
        ready = true
        draw()
      })
      .catch(() => {
        ready = true
        draw()
      })

    const draw = () => {
      const s = state.current
      const colors = {
        ocean: cssVar('--faint', '#a09a90'),
        land: cssVar('--panel', '#ffffff'),
        accent: cssVar('--accent', '#c2500d'),
        ink: cssVar('--ink', '#1b1815'),
        panel: cssVar('--panel', '#ffffff'),
      }
      ctx.clearRect(0, 0, W, H)

      if (!ready) {
        ctx.fillStyle = colors.ocean
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('Loading…', W / 2, H / 2)
        return
      }

      // Ocean dot grid.
      ctx.fillStyle = colors.ocean
      ctx.globalAlpha = 0.18
      for (let y = 14; y < H; y += 14) {
        for (let x = 14; x < W; x += 14) {
          ctx.fillRect(x, y, 1.4, 1.4)
        }
      }
      ctx.globalAlpha = 1

      // Land dot cloud.
      ctx.fillStyle = colors.land
      ctx.globalAlpha = 0.55
      for (const d of landDots) {
        ctx.fillRect(d.x, d.y, 1.3, 1.3)
      }
      ctx.globalAlpha = 1

      // Routes (dashed great-circle arcs).
      ctx.strokeStyle = colors.accent
      ctx.globalAlpha = 0.5
      ctx.lineWidth = 1
      ctx.setLineDash([3, 4])
      for (const [a, b] of ROUTES) {
        const from = CITY_COORDS[a]
        const to = CITY_COORDS[b]
        if (!from || !to) continue
        drawRoute(ctx, routePoints(from, to, landProj.project))
      }
      ctx.setLineDash([])
      ctx.globalAlpha = 1

      // Animated moving dots along routes.
      const t = (performance.now() / 1000 / 14) % 1
      ctx.fillStyle = colors.accent
      for (const [a, b] of ROUTES) {
        const from = CITY_COORDS[a]
        const to = CITY_COORDS[b]
        if (!from || !to) continue
        const [x, y] = animatedDot(from, to, landProj.project, t)
        ctx.beginPath()
        ctx.arc(x, y, 2, 0, Math.PI * 2)
        ctx.fill()
      }

      // Hotspot pins.
      for (const hs of s.hotspots) {
        const coord = CITY_COORDS[hs.city]
        if (!coord) continue
        const [x, y] = landProj.project(coord.lng, coord.lat)
        const r = Math.min(14, 4 + Math.sqrt(hs.v) * 1.1)
        const isPin = hs.city === s.pin
        const grad = ctx.createRadialGradient(x, y, 0, x, y, r * 2.2)
        grad.addColorStop(0, colors.accent)
        grad.addColorStop(1, 'transparent')
        ctx.globalAlpha = isPin ? 0.95 : 0.75
        ctx.beginPath()
        ctx.fillStyle = grad
        ctx.arc(x, y, r * 2.2, 0, Math.PI * 2)
        ctx.fill()
        ctx.globalAlpha = 1
        ctx.beginPath()
        ctx.strokeStyle = colors.accent
        ctx.lineWidth = 1.5
        ctx.arc(x, y, r, 0, Math.PI * 2)
        ctx.stroke()
        if (isPin) {
          ctx.beginPath()
          ctx.fillStyle = colors.accent
          ctx.arc(x, y, 3.5, 0, Math.PI * 2)
          ctx.fill()
        }
      }
    }

    const loop = () => {
      if (!destroyed) {
        draw()
        animFrame = requestAnimationFrame(loop)
      }
    }
    animFrame = requestAnimationFrame(loop)

    const offTheme = onThemeChange(draw)
    const onResize = () => {
      const dpr = Math.min(2, window.devicePixelRatio || 1)
      canvas.width = W * dpr
      canvas.height = H * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      draw()
    }
    onResize()

    const onClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      if (rect.width === 0) return
      const mx = ((e.clientX - rect.left) / rect.width) * W
      const my = ((e.clientY - rect.top) / rect.height) * H
      for (const hs of state.current.hotspots) {
        const coord = CITY_COORDS[hs.city]
        if (!coord) continue
        const [x, y] = landProj.project(coord.lng, coord.lat)
        const r = Math.min(14, 4 + Math.sqrt(hs.v) * 1.1) * 2.2
        if (Math.hypot(mx - x, my - y) <= r) {
          onPick(hs.city)
          return
        }
      }
    }
    canvas.addEventListener('click', onClick)

    return () => {
      destroyed = true
      cancelAnimationFrame(animFrame)
      offTheme()
      window.removeEventListener('resize', onResize)
      canvas.removeEventListener('click', onClick)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="mapwrap" id="mapwrap" ref={wrapRef}>
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%', display: 'block', cursor: 'pointer' }}
        aria-label="World map of order volume hotspots"
      />
      <div className="maplegend">
        <i />
        order volume
      </div>
    </div>
  )
}

function drawRoute(ctx: CanvasRenderingContext2D, pts: [number, number][]): void {
  ctx.beginPath()
  pts.forEach(([x, y], i) => {
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.stroke()
}
