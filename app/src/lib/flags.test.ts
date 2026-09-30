import { describe, expect, it } from 'vitest'
import type { TeamsFile } from '../data/types'
import { flagCount, flagUrl } from './flags'

// Every generated teams.json, read through Vite so the test needs no Node types
const TEAM_FILES = import.meta.glob<TeamsFile>('/public/data/*/teams.json', { import: 'default', eager: true })

describe('flags (D39)', () => {
  it('bundles the flag-icons set', () => {
    expect(flagCount()).toBeGreaterThan(250)
    expect(flagUrl('gb-eng')).toBeTruthy()
    expect(flagUrl('xk')).toBeTruthy()
    expect(flagUrl('nope')).toBeNull()
  })

  it('has a flag for every nationCode in the generated data', () => {
    const files = Object.values(TEAM_FILES)
    expect(files).toHaveLength(10)
    const missing = new Set<string>()
    for (const file of files) {
      for (const team of file.teams) {
        for (const p of team.xi) {
          if (!flagUrl(p.nationCode)) missing.add(`${p.nation} (${p.nationCode})`)
        }
      }
    }
    expect([...missing]).toEqual([])
  })
})
