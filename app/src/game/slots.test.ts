import { describe, expect, it } from 'vitest'
import { ROUND_COUNT, SLOTS, SLOT_POSITIONS } from './slots'

describe('slots', () => {
  it('has 11 slots in round order: GK, defence, midfield, attack (D8)', () => {
    expect(SLOTS).toEqual(['GK', 'LB', 'LCB', 'RCB', 'RB', 'LCM', 'CM', 'RCM', 'LW', 'ST', 'RW'])
    expect(ROUND_COUNT).toBe(11)
  })

  it('places the GK at the bottom and each line left to right (D29)', () => {
    const y = (s: keyof typeof SLOT_POSITIONS) => SLOT_POSITIONS[s].y
    const x = (s: keyof typeof SLOT_POSITIONS) => SLOT_POSITIONS[s].x
    expect(y('GK')).toBeGreaterThan(y('LCB'))
    expect(y('LCB')).toBeGreaterThan(y('CM'))
    expect(y('CM')).toBeGreaterThan(y('ST'))
    expect([x('LB'), x('LCB'), x('RCB'), x('RB')]).toEqual([...[x('LB'), x('LCB'), x('RCB'), x('RB')]].sort((a, b) => a - b))
    expect(x('LCM')).toBeLessThan(x('CM'))
    expect(x('CM')).toBeLessThan(x('RCM'))
    expect(x('LW')).toBeLessThan(x('ST'))
    expect(x('ST')).toBeLessThan(x('RW'))
  })
})
