import type { Slot } from '../data/types'

// Round order (D8): GK, then defence, midfield and attack, left to right. Same order as the data.
export const SLOTS: readonly Slot[] = ['GK', 'LB', 'LCB', 'RCB', 'RB', 'LCM', 'CM', 'RCM', 'LW', 'ST', 'RW']

// Slot centres on a vertical pitch (D29), in percent of pitch width (x) and height (y, 0 = top).
// Attack is at the top, the goalkeeper at the bottom.
export const SLOT_POSITIONS: Record<Slot, { x: number; y: number }> = {
  LW: { x: 17, y: 15 },
  ST: { x: 50, y: 11 },
  RW: { x: 83, y: 15 },
  LCM: { x: 24, y: 40 },
  CM: { x: 50, y: 44 },
  RCM: { x: 76, y: 40 },
  LB: { x: 12, y: 66 },
  LCB: { x: 37.5, y: 70 },
  RCB: { x: 62.5, y: 70 },
  RB: { x: 88, y: 66 },
  GK: { x: 50, y: 89 },
}

export const ROUND_COUNT = SLOTS.length
