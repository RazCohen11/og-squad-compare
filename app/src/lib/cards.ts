// Display helpers for player cards

export type Tier = 'bronze' | 'silver' | 'gold'

// Card tier by rating, as in FUT (D37): bronze ≤ 64, silver 65–74, gold ≥ 75
export function tierFor(ovr: number): Tier {
  if (ovr >= 75) return 'gold'
  if (ovr >= 65) return 'silver'
  return 'bronze'
}

// Leading initials such as "L. " or "J. M. " in a short name
const LEADING_INITIALS = /^(?:\p{Lu}\.\s*)+/u

// Short display form for mini cards: "L. Messi" → "Messi", "M. ter Stegen" → "ter Stegen",
// "Cristiano Ronaldo" and "Vini Jr." stay as they are
export function displayName(shortName: string): string {
  const stripped = shortName.replace(LEADING_INITIALS, '').trim()
  return stripped || shortName
}

// Two-letter avatar initials (D22, no photos): "L. Messi" → "LM", "Cristiano Ronaldo" → "CR", "Rodri" → "RO"
export function initials(shortName: string): string {
  const words = shortName
    .replace(/[.]/g, ' ')
    .split(/\s+/)
    .filter((w) => /\p{L}/u.test(w))
  if (words.length === 0) return '?'
  if (words.length === 1) return words[0].slice(0, 2).toLocaleUpperCase()
  const first = words[0][0]
  // Skip lowercase particles such as "ter" or "van" for the second letter when possible
  const last = [...words.slice(1)].reverse().find((w) => w[0] === w[0].toLocaleUpperCase()) ?? words[words.length - 1]
  return (first + last[0]).toLocaleUpperCase()
}
