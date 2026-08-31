import { useEffect, useRef } from 'react'

type RGB = [number, number, number]

const REDUCED_MOTION =
  typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches

let cssCache: Record<string, string> = {}
if (typeof window !== 'undefined') {
  const clearCache = () => {
    cssCache = {}
  }
  window.addEventListener('kit:theme', clearCache)
  if (typeof MutationObserver !== 'undefined') {
    new MutationObserver(clearCache).observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    })
  }
}

function cssVarCached(name: string): string {
  if (name in cssCache) return cssCache[name]
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  cssCache[name] = value
  return value
}

export function parseColor(raw: string): RGB {
  if (!raw) return [128, 128, 128]
  const s = raw.trim()
  if (s[0] === '#') {
    const hex =
      s.length === 4 ? s.slice(1).split('').map((c) => c + c).join('') : s.slice(1)
    return [
      parseInt(hex.slice(0, 2), 16),
      parseInt(hex.slice(2, 4), 16),
      parseInt(hex.slice(4, 6), 16),
    ]
  }
  if (/^color\(|^oklch|^lab/.test(s)) {
    const probe = document.createElement('canvas').getContext('2d')
    if (probe) {
      probe.fillStyle = s
      return parseColor(probe.fillStyle)
    }
  }
  const nums = (s.match(/[\d.]+/g) || []).map(Number)
  return nums.length >= 3 ? [nums[0], nums[1], nums[2]] : [128, 128, 128]
}

type GlCtx = WebGLRenderingContext | WebGL2RenderingContext
type DrawFn = (hitbox: GlowHitbox, timeSec: number) => void

interface GlowHitbox {
  cv: HTMLCanvasElement
  ctx: GlCtx
  w: number
  h: number
  dpr: number
  host: HTMLElement
  t: number
  el: HTMLCanvasElement
  onsize?: (w: number, h: number) => void
  start(): void
  stop(): void
  destroy(): void
}

interface VitOptions {
  alpha?: boolean
  gl?: boolean
  scale?: number
  fps?: number
}

function vit(host: HTMLElement, render: DrawFn, opts: VitOptions = {}): GlowHitbox | null {
  const { alpha = true, gl = false, scale = 1, fps = 0 } = opts
  const canvas = document.createElement('canvas')
  canvas.style.cssText =
    'position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none'
  host.appendChild(canvas)
  if (getComputedStyle(host).position === 'static') host.style.position = 'relative'

  let ctx: GlCtx | null = null
  if (gl) {
    ctx =
      (canvas.getContext('webgl2', { alpha, antialias: false }) as GlCtx | null) ||
      (canvas.getContext('webgl', { alpha }) as GlCtx | null)
  } else {
    ctx = canvas.getContext('2d', { alpha }) as GlCtx | null
  }
  if (!ctx) {
    canvas.remove()
    return null
  }

  let w = 0
  let h = 0
  let dpr = 1
  let raf = 0
  let start = performance.now()
  let running = false
  let visible = true
  let pageHidden = false
  let last = -1e9

  const resize = () => {
    const rect = host.getBoundingClientRect()
    dpr = Math.min(devicePixelRatio || 1, 2) * scale
    w = Math.max(1, rect.width)
    h = Math.max(1, rect.height)
    canvas.width = (w * dpr) | 0
    canvas.height = (h * dpr) | 0
    if (gl) ctx!.viewport(0, 0, canvas.width, canvas.height)
    else (ctx as unknown as CanvasRenderingContext2D).setTransform(dpr, 0, 0, dpr, 0, 0)
    hit.w = w
    hit.h = h
    hit.dpr = dpr
    hit.onsize?.(w, h)
  }

  const frameGap = fps ? 1000 / fps - 1 : 0

  const loop = (ts: number) => {
    raf = requestAnimationFrame(loop)
    if (!(ts - last < frameGap)) {
      last = ts
      render(hit, (ts - start) / 1000)
    }
  }

  const hit: GlowHitbox = {
    cv: canvas,
    ctx,
    w,
    h,
    dpr,
    host,
    t: 0,
    el: canvas,
    start() {
      if (!running && visible && !pageHidden) {
        running = true
        start = performance.now() - hit.t * 1000 || performance.now()
        raf = requestAnimationFrame(loop)
      }
    },
    stop() {
      running = false
      cancelAnimationFrame(raf)
    },
    destroy() {
      hit.stop()
      resizeObs.disconnect()
      intersectObs.disconnect()
      window.removeEventListener('visibilitychange', onVisibility)
      canvas.remove()
    },
  }

  const resizeObs = new ResizeObserver(resize)
  resizeObs.observe(host)

  const intersectObs = new IntersectionObserver(
    (entries) => {
      visible = entries[0]?.isIntersecting ?? false
      if (visible && !pageHidden) hit.start()
      else hit.stop()
    },
    { threshold: 0 },
  )
  intersectObs.observe(host)

  const onVisibility = () => {
    pageHidden = document.hidden
    if (!pageHidden && visible) hit.start()
    else hit.stop()
  }
  window.addEventListener('visibilitychange', onVisibility)

  resize()
  if (REDUCED_MOTION) render(hit, 0)
  else hit.start()

  return hit
}

interface PitOptions {
  res?: number
  fps?: number
}

function pit(
  host: HTMLElement,
  fragSource: string,
  uniforms: (hitbox: GlowHitbox, t: number) => Record<string, number | number[]>,
  opts: PitOptions = {},
): GlowHitbox | null {
  const hit = vit(host, (p, y) => draw(p, y), { alpha: false, gl: true, scale: opts.res ?? 1, fps: opts.fps ?? 0 })
  if (!hit) return null
  const gl = hit.ctx

  const compile = (type: number, source: string) => {
    const shader = gl.createShader(type)!
    gl.shaderSource(shader, source)
    gl.compileShader(shader)
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.warn(gl.getShaderInfoLog(shader))
    }
    return shader
  }

  const program = gl.createProgram()!
  gl.attachShader(
    program,
    compile(gl.VERTEX_SHADER, 'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}'),
  )
  gl.attachShader(program, compile(gl.FRAGMENT_SHADER, fragSource))
  gl.linkProgram(program)
  gl.useProgram(program)

  const buffer = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW)
  const loc = gl.getAttribLocation(program, 'p')
  gl.enableVertexAttribArray(loc)
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)

  const uniformCache: Record<string, WebGLUniformLocation | null> = {}
  const uni = (name: string) => {
    if (!(name in uniformCache)) uniformCache[name] = gl.getUniformLocation(program, name)
    return uniformCache[name]
  }

  const draw = (p: GlowHitbox, t: number) => {
    p.t = t
    gl.uniform2f(uni('u_res'), p.cv.width, p.cv.height)
    gl.uniform1f(uni('u_t'), t)
    const values = uniforms(p, t)
    for (const key in values) {
      const value = values[key]
      if (Array.isArray(value)) {
        if (value.length === 2) gl.uniform2fv(uni(key), value)
        else if (value.length === 3) gl.uniform3fv(uni(key), value)
        else gl.uniform4fv(uni(key), value)
      } else {
        gl.uniform1f(uni(key), value)
      }
    }
    gl.drawArrays(gl.TRIANGLES, 0, 3)
  }

  return hit
}

const FRAGMENT_SOURCE = `precision highp float;
uniform vec2 u_res; uniform float u_t, u_amp, u_scale;
uniform vec3 u_bg, u_a, u_b, u_c;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1,0)), u.x),
             mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x), u.y);
}
float fbm(vec2 p){
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 3; i++){ v += a * noise(p); p *= 2.02; a *= 0.5; }
  return v;
}
void main(){
  vec2 uv = gl_FragCoord.xy / u_res;
  vec2 p = (gl_FragCoord.xy - 0.5 * u_res) / min(u_res.x, u_res.y) * u_scale;
  vec2 q = vec2(fbm(p + vec2(0.0, u_t * 0.06)), fbm(p + vec2(3.4, -u_t * 0.05)));
  vec2 r = vec2(fbm(p + 2.0 * q + vec2(1.7, 9.2) + u_t * 0.04),
                fbm(p + 2.0 * q + vec2(8.3, 2.8) - u_t * 0.03));
  float f = fbm(p + 1.8 * r);
  vec3 col = u_bg;
  col = mix(col, u_a, clamp(f * f * 1.9, 0.0, 1.0) * u_amp);
  col = mix(col, u_b, clamp(length(q) * 0.85, 0.0, 1.0) * u_amp * 0.8);
  col = mix(col, u_c, clamp(r.x * r.x * 1.4, 0.0, 1.0) * u_amp * 0.6);
  col *= 1.0 - 0.28 * length(uv - 0.5);
  col += (hash(gl_FragCoord.xy) - 0.5) / 255.0;
  gl_FragColor = vec4(col, 1.0);
}`

export interface GlowConfig {
  amp?: number
  scale?: number
  res?: number
  fps?: number
  keys?: string[]
}

export function glow(host: HTMLElement, opts: GlowConfig = {}): GlowHitbox | null {
  const { amp = 0.5, scale = 2.2, res = 0.4, fps = 30, keys = ['--fx-1', '--fx-2', '--fx-3'] } = opts
  const to01 = (value: string): RGB => {
    const [r, g, b] = parseColor(value)
    return [r / 255, g / 255, b / 255]
  }
  return pit(
    host,
    FRAGMENT_SOURCE,
    (_p) => ({
      u_amp: amp,
      u_scale: scale,
      u_bg: to01(cssVarCached('--fx-bg') || cssVarCached('--bg')),
      u_a: to01(cssVarCached(keys[0]) || cssVarCached('--accent')),
      u_b: to01(cssVarCached(keys[1]) || cssVarCached('--accent')),
      u_c: to01(cssVarCached(keys[2]) || cssVarCached('--accent')),
    }),
    { res, fps },
  )
}

export function Glow({
  amp = 0.55,
  scale = 2.6,
}: {
  amp?: number
  scale?: number
}) {
  const hostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const host = hostRef.current
    if (!host) return
    const engine = glow(host, { amp, scale })
    return () => engine?.destroy()
  }, [amp, scale])

  return <div id="glow" ref={hostRef} />
}
