import { rng } from '../lib/rng'

export interface Product {
  name: string
  sku: string
  stock: number
  reorder: number
  sold: number
  price: number
}

const PRODUCT_NAMES = [
  'Aeron cushion',
  'Kestrel desk lamp',
  'Nomad travel case',
  'Orbit wall clock',
  'Pallas floor mat',
  'Quill notebook set',
  'Ridge tumbler',
  'Solstice throw',
  'Terra planter',
  'Vellum folio',
] as const

export function generateProducts(): Product[] {
  return PRODUCT_NAMES.map((name) => ({
    name,
    sku: `SKU-${Math.round(1000 + rng() * 8999)}`,
    stock: Math.round(rng() * 260),
    reorder: 40 + Math.round(rng() * 60),
    sold: Math.round(60 + rng() * 1400),
    price: Math.round(18 + rng() * 220),
  }))
}
