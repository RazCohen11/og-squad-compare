import type { Team, VersionInfo } from '../data/types'
import type { Side } from './game'

// A picked team together with the game version it comes from (D30)
export interface GameSide {
  side: Side
  team: Team
  version: VersionInfo
}

// Compact version label for tight spots: "EA SPORTS FC 24" → "FC 24"
export function shortVersionLabel(version: VersionInfo): string {
  return version.label.replace(/^EA SPORTS\s+/, '')
}

// "FC Barcelona · FIFA 15"
export function teamLabel(side: GameSide): string {
  return `${side.team.name} · ${shortVersionLabel(side.version)}`
}
