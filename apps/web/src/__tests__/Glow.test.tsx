import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import App from '../App'

beforeEach(() => {
  vi.spyOn(window, 'requestAnimationFrame').mockImplementation(() => 0)
  vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => {})
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('Glow background (origin parity)', () => {
  it('renders the #glow host element exactly as the origin does', () => {
    render(<App />)
    expect(document.getElementById('glow')).toBeInTheDocument()
    expect(document.getElementById('glow')?.children.length).toBe(0)
  })

  it('renders #glow before the .app shell, matching the origin DOM order', () => {
    render(<App />)
    const glow = document.getElementById('glow')
    const app = document.querySelector('.app')
    const glowIndex = glow ? [...document.body.querySelectorAll('*')].indexOf(glow) : -1
    const appIndex = app ? [...document.body.querySelectorAll('*')].indexOf(app) : -1
    expect(glowIndex).toBeGreaterThanOrEqual(0)
    expect(appIndex).toBeGreaterThan(glowIndex)
  })

  it('degrades gracefully when WebGL is unavailable (jsdom getContext returns null)', () => {
    render(<App />)
    // No crash; engine removed its canvas and left no stray canvas in the host.
    expect(document.getElementById('glow')).toBeInTheDocument()
    expect(document.getElementById('glow')?.querySelector('canvas')).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
