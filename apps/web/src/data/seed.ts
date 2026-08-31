// Shared pool values + seeded generators for all data modules.

import { rng, pick } from '../lib/rng'

// Customer name parts (mirrors the reference pools).
export const FIRST_NAMES = [
  'Maya', 'Idris', 'Chen', 'Lucia', 'Tomas', 'Aisha', 'Noor', 'Petra',
  'Kwame', 'Hana', 'Elias', 'Rin', 'Sofia', 'Marek', 'Zaid', 'Ines',
] as const

export const LAST_NAMES = [
  'Okafor', 'Lindqvist', 'Duarte', 'Novak', 'Haddad', 'Yamamoto', 'Silva',
  'Kovacs', 'Mbeki', 'Aalto', 'Rossi', 'Varga', 'Nakamura', 'Weber', 'Costa', 'Bauer',
] as const

export const PLANS = ['Starter', 'Business', 'Business', 'Enterprise'] as const

// Order status pool weighted toward Paid.
export const ORDER_STATUSES = ['Paid', 'Paid', 'Paid', 'Pending', 'Pending', 'Refunded'] as const

// ~40 worldwide cities used for orders and driving the map hotspots.
export const CITIES = [
  'New York', 'Chicago', 'Los Angeles', 'Mexico City', 'Bogotá', 'Lima', 'São Paulo',
  'Rio de Janeiro', 'Buenos Aires', 'Santiago', 'Lisbon', 'Madrid', 'Barcelona', 'Rome',
  'Athens', 'Istanbul', 'Casablanca', 'Cairo', 'Lagos', 'Nairobi', 'Johannesburg',
  'Cape Town', 'Dubai', 'Mumbai', 'Bangkok', 'Kuala Lumpur', 'Ho Chi Minh City',
  'Jakarta', 'Manila', 'Singapore', 'Hong Kong', 'Shanghai', 'Beijing',
] as const

export type Plan = (typeof PLANS)[number]
export type OrderStatus = (typeof ORDER_STATUSES)[number]

// Longitude/latitude for map city pins.
export interface CityCoords {
  lng: number
  lat: number
}

export const CITY_COORDS: Record<string, CityCoords> = {
  'New York': { lng: -74.0, lat: 40.7 },
  Chicago: { lng: -87.6, lat: 41.9 },
  'Los Angeles': { lng: -118.2, lat: 34.0 },
  'Mexico City': { lng: -99.1, lat: 19.4 },
  'Bogotá': { lng: -74.1, lat: 4.6 },
  Lima: { lng: -77.0, lat: -12.0 },
  'São Paulo': { lng: -46.6, lat: -23.5 },
  'Rio de Janeiro': { lng: -43.2, lat: -22.9 },
  'Buenos Aires': { lng: -58.4, lat: -34.6 },
  Santiago: { lng: -70.7, lat: -33.4 },
  Lisbon: { lng: -9.1, lat: 38.7 },
  Madrid: { lng: -3.7, lat: 40.4 },
  Barcelona: { lng: 2.2, lat: 41.4 },
  Rome: { lng: 12.5, lat: 41.9 },
  Athens: { lng: 23.7, lat: 38.0 },
  Istanbul: { lng: 29.0, lat: 41.0 },
  Casablanca: { lng: -7.6, lat: 33.6 },
  Cairo: { lng: 31.2, lat: 30.0 },
  Lagos: { lng: 3.4, lat: 6.5 },
  Nairobi: { lng: 36.8, lat: -1.3 },
  Johannesburg: { lng: 28.0, lat: -26.2 },
  'Cape Town': { lng: 18.4, lat: -33.9 },
  Dubai: { lng: 55.3, lat: 25.2 },
  Mumbai: { lng: 72.9, lat: 19.1 },
  Bangkok: { lng: 100.5, lat: 13.8 },
  'Kuala Lumpur': { lng: 101.7, lat: 3.1 },
  'Ho Chi Minh City': { lng: 106.7, lat: 10.8 },
  Jakarta: { lng: 106.8, lat: -6.2 },
  Manila: { lng: 121.0, lat: 14.6 },
  Singapore: { lng: 103.8, lat: 1.4 },
  'Hong Kong': { lng: 114.2, lat: 22.3 },
  Shanghai: { lng: 121.5, lat: 31.2 },
  Beijing: { lng: 116.4, lat: 39.9 },
}

// Routes (city pairs) drawn as dashed great-circle arcs with animated dots.
export const ROUTES: [string, string][] = [
  ['Shanghai', 'Rome'],
  ['New York', 'Lisbon'],
  ['Singapore', 'Sydney'],
  ['Dubai', 'Cairo'],
  ['Hong Kong', 'Athens'],
  ['Singapore', 'Rome'],
  ['Mexico City', 'Madrid'],
  ['Beijing', 'Istanbul'],
  ['New York', 'London'],
  ['Los Angeles', 'Tokyo'],
  ['Bangkok', 'Amsterdam'],
  ['Cape Town', 'Paris'],
  ['Mumbai', 'Milan'],
  ['Singapore', 'New York'],
  ['Rio de Janeiro', 'Lisbon'],
]

function sampleCustomerName(): { name: string; initials: string } {
  const first = pick(FIRST_NAMES)
  const last = pick(LAST_NAMES)
  return { name: `${first} ${last}`, initials: `${first[0]}${last[0]}` }
}

export function customerName(): { name: string; initials: string } {
  return sampleCustomerName()
}

export function poolRng(): () => number {
  return rng
}
