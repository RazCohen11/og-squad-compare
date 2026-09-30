import { describe, expect, it } from 'vitest'
import type { League, Team } from '../data/types'
import { filterGroups, groupTeamsByLeague, normalizeForSearch, sortVersionsNewestFirst } from './teams'

const leagues: League[] = [
  { id: 13, name: 'Premier League' },
  { id: 53, name: 'La Liga' },
  { id: 19, name: 'Bundesliga' },
]

function team(id: number, name: string, leagueId: number): Team {
  return { id, name, leagueId, ovr: 80, eaFormation: '4-3-3', xi: [] }
}

const teams = [
  team(10, 'Manchester City', 13),
  team(21, 'FC Bayern München', 19),
  team(1, 'Arsenal', 13),
  team(243, 'Real Madrid', 53),
  team(240, 'Atlético Madrid', 53),
]

describe('groupTeamsByLeague', () => {
  it('follows the league order and sorts clubs alphabetically', () => {
    const groups = groupTeamsByLeague(teams, leagues)
    expect(groups.map((g) => g.league.name)).toEqual(['Premier League', 'La Liga', 'Bundesliga'])
    expect(groups[0].teams.map((t) => t.name)).toEqual(['Arsenal', 'Manchester City'])
    expect(groups[1].teams.map((t) => t.name)).toEqual(['Atlético Madrid', 'Real Madrid'])
  })

  it('drops leagues without clubs', () => {
    const groups = groupTeamsByLeague(teams.slice(0, 1), leagues)
    expect(groups).toHaveLength(1)
  })
})

describe('filterGroups', () => {
  const groups = groupTeamsByLeague(teams, leagues)

  it('matches case- and accent-insensitively', () => {
    expect(filterGroups(groups, 'munchen').flatMap((g) => g.teams.map((t) => t.id))).toEqual([21])
    expect(filterGroups(groups, 'ATLETICO').flatMap((g) => g.teams.map((t) => t.id))).toEqual([240])
  })

  it('keeps every league a match is in and drops the rest', () => {
    const result = filterGroups(groups, 'madrid')
    expect(result.map((g) => g.league.id)).toEqual([53])
    expect(result[0].teams).toHaveLength(2)
  })

  it('returns everything for an empty query', () => {
    expect(filterGroups(groups, '   ')).toBe(groups)
  })
})

describe('helpers', () => {
  it('normalizes text for search', () => {
    expect(normalizeForSearch('  Borussia Mönchengladbach ')).toBe('borussia monchengladbach')
  })

  it('sorts versions newest first without mutating the input', () => {
    const input = [{ id: 15 }, { id: 24 }, { id: 19 }]
    expect(sortVersionsNewestFirst(input).map((v) => v.id)).toEqual([24, 19, 15])
    expect(input.map((v) => v.id)).toEqual([15, 24, 19])
  })
})
