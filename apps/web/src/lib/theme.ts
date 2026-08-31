// Theme management: light/dark via data-theme attribute, persisted in localStorage.

const THEME_KEY = 'kit-theme'

export type ThemeMode = 'light' | 'dark'

export function getTheme(): ThemeMode {
  if (typeof document === 'undefined') return 'dark'
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'
}

export function setTheme(mode: ThemeMode): void {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute('data-theme', mode)
  try {
    localStorage.setItem(THEME_KEY, mode)
  } catch {
    /* ignore */
  }
}

export function initTheme(): ThemeMode {
  let stored: string | null = null
  try {
    stored = localStorage.getItem(THEME_KEY)
  } catch {
    /* ignore */
  }
  const initial: ThemeMode = stored === 'light' || stored === 'dark' ? stored : 'dark'
  setTheme(initial)
  return initial
}

// Updates every chart instance when the theme changes. Chart manager registers here.
type ThemeListener = () => void
const listeners = new Set<ThemeListener>()

export function onThemeChange(fn: ThemeListener): () => void {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

export function toggleTheme(): ThemeMode {
  const next: ThemeMode = getTheme() === 'dark' ? 'light' : 'dark'
  setTheme(next)
  listeners.forEach((fn) => fn())
  return next
}

// Read a CSS variable from the root, for ECharts base option theming.
export function cssVar(name: string, fallback = ''): string {
  if (typeof getComputedStyle === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

// Tiny localStorage-backed value for settings.
export function loadSetting(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function saveSetting(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* ignore */
  }
}
