// Seeded PRNG (mulberry32) for deterministic mock data generation.
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0
  return function () {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// Fully seedable RNG used across all data generators.
export const SEED = 20260815

export const rng = mulberry32(SEED)

// Deterministic picker from an array.
export function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(rng() * arr.length)]
}
