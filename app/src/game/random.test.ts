import { describe, expect, it } from 'vitest'
import type { IndexEntry } from '../data/types'
import {
  RANDOM_HISTORY,
  RANDOM_MAX_AVG_DIFF,
  RANDOM_MIN_XI_AVG,
  RandomMatchupError,
  opponentsFor,
  pairKey,
  pickRandomMatchup,
  randomPool,
  rememberMatchup,
  seededRandom,
  teamKey,
} from './random'

// The real generated index, read through Vite
const REAL_INDEX = Object.values(
  import.meta.glob<IndexEntry[]>('/public/data/index.json', { import: 'default', eager: true }),
)[0]

function team(v: number, id: number, xiAvg: number, name = `T${id}`): IndexEntry {
  return { v, id, name, leagueId: 13, xiAvg }
}

// Small synthetic index: Barcelona appears in two versions with the same id
const SMALL: IndexEntry[] = [
  team(15, 241, 85.0, 'FC Barcelona'),
  team(19, 241, 85.5, 'FC Barcelona'),
  team(17, 243, 86.0, 'Real Madrid'),
  team(20, 21, 84.2, 'Bayern'),
  team(22, 10, 79.99, 'Just below the threshold'),
  team(18, 5, 70.0, 'Weak'),
  team(24, 9, 90.0, 'Far away'),
]

describe('config (D46–D48)', () => {
  it('has the agreed values', () => {
    expect(RANDOM_MIN_XI_AVG).toBe(80)
    expect(RANDOM_MAX_AVG_DIFF).toBe(1.0)
    expect(RANDOM_HISTORY).toBe(10)
  })
})

describe('randomPool', () => {
  it('keeps only teams with xiAvg >= 80', () => {
    const pool = randomPool(SMALL)
    expect(pool.every((t) => t.xiAvg >= 80)).toBe(true)
    expect(pool.map((t) => t.name)).not.toContain('Just below the threshold')
    expect(pool).toHaveLength(5)
  })
})

describe('pickRandomMatchup', () => {
  it('respects the threshold and the difference on many seeded picks of the real index', () => {
    const random = seededRandom(1)
    for (let i = 0; i < 500; i++) {
      const { a, b } = pickRandomMatchup(REAL_INDEX, { random })
      expect(a.xiAvg).toBeGreaterThanOrEqual(80)
      expect(b.xiAvg).toBeGreaterThanOrEqual(80)
      expect(Math.abs(a.xiAvg - b.xiAvg)).toBeLessThanOrEqual(1.0 + 1e-9)
      expect(teamKey(a)).not.toBe(teamKey(b))
    }
  })

  it('never pairs the same club in the same version, but allows it across versions', () => {
    const random = seededRandom(2)
    let sameClubOtherVersion = 0
    for (let i = 0; i < 300; i++) {
      const { a, b } = pickRandomMatchup(SMALL, { random })
      expect(a.v === b.v && a.id === b.id).toBe(false)
      if (a.id === b.id) sameClubOtherVersion++
    }
    // Barcelona 15 vs Barcelona 19 (85.0 vs 85.5) is a valid pair and must come up
    expect(sameClubOtherVersion).toBeGreaterThan(0)
  })

  it('swaps sides, so the stronger team is not always A', () => {
    const random = seededRandom(3)
    let strongerIsA = 0
    let strongerIsB = 0
    for (let i = 0; i < 400; i++) {
      const { a, b } = pickRandomMatchup(REAL_INDEX, { random })
      if (a.xiAvg > b.xiAvg) strongerIsA++
      if (b.xiAvg > a.xiAvg) strongerIsB++
    }
    expect(strongerIsA).toBeGreaterThan(100)
    expect(strongerIsB).toBeGreaterThan(100)
  })

  it('does not repeat a pair from the last RANDOM_HISTORY matchups, in either order', () => {
    const random = seededRandom(4)
    let history: string[] = []
    const recent: string[] = []
    for (let i = 0; i < 200; i++) {
      const m = pickRandomMatchup(REAL_INDEX, { random, history })
      const key = pairKey(m.a, m.b)
      expect(recent.slice(-RANDOM_HISTORY)).not.toContain(key)
      recent.push(key)
      history = rememberMatchup(history, m)
      expect(history.length).toBeLessThanOrEqual(RANDOM_HISTORY)
    }
  })

  it('history blocks a pair even when it is the only one, then re-picks A or fails clearly', () => {
    // Only Barcelona 15 / Barcelona 19 / Real 17 are within 1.0 of each other here
    const tiny = [team(15, 241, 85.0), team(19, 241, 85.5), team(17, 243, 86.0)]
    const history = [pairKey(tiny[0], tiny[1]), pairKey(tiny[1], tiny[2])]
    // Only valid pair left: Barcelona 15 (85.0) vs Real 17 (86.0)
    for (let seed = 0; seed < 20; seed++) {
      const { a, b } = pickRandomMatchup(tiny, { random: seededRandom(seed), history })
      expect(pairKey(a, b)).toBe(pairKey(tiny[0], tiny[2]))
    }
    const all = [...history, pairKey(tiny[0], tiny[2])]
    expect(() => pickRandomMatchup(tiny, { random: seededRandom(1), history: all })).toThrow(RandomMatchupError)
  })

  it('fails clearly with a too small pool or no pair within the difference', () => {
    expect(() => pickRandomMatchup([team(15, 1, 85)])).toThrow(/Not enough teams/)
    expect(() => pickRandomMatchup([team(15, 1, 85), team(15, 2, 70)])).toThrow(/Not enough teams/)
    expect(() => pickRandomMatchup([team(15, 1, 82), team(16, 2, 85)])).toThrow(RandomMatchupError)
  })

  it('treats a difference of exactly 1.0 as similar despite float error', () => {
    const a = team(15, 1, 81.27)
    const b = team(16, 2, 80.27)
    expect(opponentsFor(a, [a, b])).toEqual([b])
  })

  it('is deterministic for a given seed', () => {
    const first = pickRandomMatchup(REAL_INDEX, { random: seededRandom(42) })
    const second = pickRandomMatchup(REAL_INDEX, { random: seededRandom(42) })
    expect(second).toEqual(first)
  })
})

describe('rememberMatchup', () => {
  it('keeps the last N pair keys in order', () => {
    let history: string[] = []
    for (let i = 0; i < 15; i++) history = rememberMatchup(history, { a: team(15, i, 85), b: team(16, i, 85) })
    expect(history).toHaveLength(RANDOM_HISTORY)
    expect(history[0]).toBe(pairKey(team(15, 5, 85), team(16, 5, 85)))
  })
})
