import type { League, Team } from '../data/types'

export interface LeagueGroup {
  league: League
  teams: Team[]
}

// Lower-case and strip accents, so "munchen" finds "München"
export function normalizeForSearch(text: string): string {
  return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()
}

// Groups teams by league in the given league order; clubs are alphabetical inside a league
export function groupTeamsByLeague(teams: Team[], leagues: League[]): LeagueGroup[] {
  return leagues
    .map((league) => ({
      league,
      teams: teams
        .filter((t) => t.leagueId === league.id)
        .sort((a, b) => a.name.localeCompare(b.name)),
    }))
    .filter((group) => group.teams.length > 0)
}

// Keeps clubs whose name contains the query (case- and accent-insensitive); drops empty leagues
export function filterGroups(groups: LeagueGroup[], query: string): LeagueGroup[] {
  const q = normalizeForSearch(query)
  if (!q) return groups
  return groups
    .map((group) => ({
      league: group.league,
      teams: group.teams.filter((t) => normalizeForSearch(t.name).includes(q)),
    }))
    .filter((group) => group.teams.length > 0)
}

// Newest version first
export function sortVersionsNewestFirst<T extends { id: number }>(versions: T[]): T[] {
  return [...versions].sort((a, b) => b.id - a.id)
}
