// Random matchup mode (D45–D49): pure logic, no React and no I/O.

import type { IndexEntry } from '../data/types'

// Tuning knobs, kept in one place
// Pool = teams whose Best XI averages at least this (D46)
export const RANDOM_MIN_XI_AVG = 80
// Opponents must be within this many points of XI average (D47)
export const RANDOM_MAX_AVG_DIFF = 1.0
// A pair is not repeated within this many random matchups of a session (D48)
export const RANDOM_HISTORY = 10
// Random re-picks of Team A before falling back to an exhaustive search
const MAX_ATTEMPTS = 50
// XI averages have 2 decimals; this absorbs float error in "diff <= 1.0" checks (e.g. 81.27 - 80.27)
const EPSILON = 1e-9

// A random number in [0, 1), like Math.random; injectable so tests are deterministic
export type RandomSource = () => number

export interface Matchup {
  a: IndexEntry
  b: IndexEntry
}

export class RandomMatchupError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'RandomMatchupError'
  }
}

export interface PickOptions {
  random?: RandomSource
  // Pair keys of recent random matchups, oldest first (see pairKey / rememberMatchup)
  history?: readonly string[]
  minAvg?: number
  maxDiff?: number
}

// Identity of a team in one version; the same club in another version is a different team (D48)
export function teamKey(t: IndexEntry): string {
  return `${t.v}:${t.id}`
}

// Order-independent key of a pair
export function pairKey(a: IndexEntry, b: IndexEntry): string {
  return [teamKey(a), teamKey(b)].sort().join('|')
}

export function randomPool(index: readonly IndexEntry[], minAvg = RANDOM_MIN_XI_AVG): IndexEntry[] {
  return index.filter((t) => t.xiAvg >= minAvg - EPSILON)
}

export function opponentsFor(
  a: IndexEntry,
  pool: readonly IndexEntry[],
  maxDiff = RANDOM_MAX_AVG_DIFF,
  history: readonly string[] = [],
): IndexEntry[] {
  const recent = new Set(history)
  return pool.filter(
    (b) =>
      teamKey(b) !== teamKey(a) && Math.abs(a.xiAvg - b.xiAvg) <= maxDiff + EPSILON && !recent.has(pairKey(a, b)),
  )
}

function pickOne<T>(items: readonly T[], random: RandomSource): T {
  return items[Math.min(items.length - 1, Math.floor(random() * items.length))]
}

// Picks Team A uniformly from the pool, then B uniformly from A's valid opponents, then randomly swaps
// sides so the stronger team is not always A. Throws RandomMatchupError if no valid pair exists.
export function pickRandomMatchup(index: readonly IndexEntry[], options: PickOptions = {}): Matchup {
  const random = options.random ?? Math.random
  const history = options.history ?? []
  const maxDiff = options.maxDiff ?? RANDOM_MAX_AVG_DIFF
  const pool = randomPool(index, options.minAvg ?? RANDOM_MIN_XI_AVG)
  if (pool.length < 2) {
    throw new RandomMatchupError(`Not enough teams for a random matchup (${pool.length} in the pool).`)
  }

  let a = pickOne(pool, random)
  let candidates = opponentsFor(a, pool, maxDiff, history)
  // If A has no valid opponent, re-pick A (bounded)
  for (let attempt = 1; attempt < MAX_ATTEMPTS && candidates.length === 0; attempt++) {
    a = pickOne(pool, random)
    candidates = opponentsFor(a, pool, maxDiff, history)
  }
  if (candidates.length === 0) {
    // Random re-picks were unlucky: choose among the teams that do have an opponent, if any
    const viable = pool.filter((t) => opponentsFor(t, pool, maxDiff, history).length > 0)
    if (viable.length === 0) {
      throw new RandomMatchupError('No valid random matchup is left. Try again later or pick the teams yourself.')
    }
    a = pickOne(viable, random)
    candidates = opponentsFor(a, pool, maxDiff, history)
  }

  const b = pickOne(candidates, random)
  return random() < 0.5 ? { a, b } : { a: b, b: a }
}

// Returns the history with this matchup added, keeping only the last `limit` pairs
export function rememberMatchup(history: readonly string[], matchup: Matchup, limit = RANDOM_HISTORY): string[] {
  return [...history, pairKey(matchup.a, matchup.b)].slice(-limit)
}

// Small seeded generator (mulberry32) for tests and reproducible samples
export function seededRandom(seed: number): RandomSource {
  let s = seed >>> 0
  return () => {
    s = (s + 0x6d2b79f5) >>> 0
    let t = s
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
