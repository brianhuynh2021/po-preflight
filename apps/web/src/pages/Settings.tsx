import { useState } from 'react'
import { Panel } from '../components/Panel'
import { Seg } from '../components/Seg'
import { Sw } from '../components/Sw'
import { getTheme, loadSetting, saveSetting, setTheme, type ThemeMode } from '../lib/theme'

const SETTINGS: { key: string; label: string; hint: string; def: boolean }[] = [
  { key: 'digest', label: 'Email digest', hint: 'Weekly summary of store health', def: false },
  { key: 'alerts', label: 'Threshold alerts', hint: 'Notify me on low stock and refunds', def: true },
  { key: 'beta', label: 'Beta features', hint: 'Opt in to unreleased modules', def: false },
]

function loadBool(key: string, def: boolean): boolean {
  const raw = loadSetting(`nw-${key}`)
  if (raw == null) return def
  return raw === 'true'
}

export function SettingsPage() {
  const [toggles, setToggles] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(SETTINGS.map((s) => [s.key, loadBool(s.key, s.def)])),
  )
  const [rows, setRows] = useState(() => Number(loadSetting('nw-rows') || '8'))
  const [density, setDensity] = useState<'comfortable' | 'compact'>(() =>
    (loadSetting('nw-density') as 'comfortable' | 'compact' | null) ?? 'comfortable',
  )
  const [theme, setThemeState] = useState<ThemeMode>(getTheme())

  const toggle = (key: string, next: boolean) => {
    saveSetting(`nw-${key}`, String(next))
    setToggles((t) => ({ ...t, [key]: next }))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <Panel title="Appearance">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '13px 20px', borderBottom: '1px solid var(--line-soft)' }}>
          <div>
            <div style={{ fontWeight: 520 }}>Theme</div>
            <div className="faint" style={{ fontSize: 11.5 }}>
              Switch between light and dark
            </div>
          </div>
          <Seg<ThemeMode>
            id="themeSeg"
            options={[
              { value: 'light', label: 'Light' },
              { value: 'dark', label: 'Dark' },
            ]}
            value={theme}
            onChange={(t) => {
              setTheme(t)
              setThemeState(t)
            }}
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '13px 20px', borderBottom: '1px solid var(--line-soft)' }}>
          <div>
            <div style={{ fontWeight: 520 }}>Density</div>
            <div className="faint" style={{ fontSize: 11.5 }}>
              Table and list spacing
            </div>
          </div>
          <Seg<'comfortable' | 'compact'>
            id="densSeg"
            options={[
              { value: 'comfortable', label: 'Comfortable' },
              { value: 'compact', label: 'Compact' },
            ]}
            value={density}
            onChange={(d) => {
              setDensity(d)
              saveSetting('nw-density', d)
            }}
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '13px 20px' }}>
          <div>
            <div style={{ fontWeight: 520 }}>Rows per page</div>
            <div className="faint" style={{ fontSize: 11.5 }}>
              Default rows shown in tables
            </div>
          </div>
          <input
            id="rows"
            type="number"
            min={4}
            max={50}
            value={rows}
            style={{ width: 72 }}
            onChange={(e) => {
              const v = Number(e.target.value)
              if (v >= 1) {
                setRows(v)
                saveSetting('nw-rows', String(v))
              }
            }}
          />
        </div>
      </Panel>

      <Panel title="Notifications">
        <div className="form">
          {SETTINGS.map((s) => (
            <div className="frow" key={s.key}>
              <div className="fl">
                <div className="t">{s.label}</div>
                <div className="h">{s.hint}</div>
              </div>
              <Sw k={s.key} on={toggles[s.key] ?? false} onToggle={(n) => toggle(s.key, n)} />
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
