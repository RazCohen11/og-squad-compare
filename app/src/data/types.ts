// Types mirroring app/public/data/versions.json and app/public/data/<version>/teams.json
// (format defined in docs/prompts/02-pipeline.md §2).

// The 11 slots of the canonical 4-3-3, in data order (also the round order, D8)
export type Slot = 'GK' | 'LB' | 'LCB' | 'RCB' | 'RB' | 'LCM' | 'CM' | 'RCM' | 'LW' | 'ST' | 'RW'
export type OutfieldSlot = Exclude<Slot, 'GK'>

// Generic positions as they appear in `player_positions`
export type Position =
  | 'GK'
  | 'CB' | 'LB' | 'RB' | 'LWB' | 'RWB'
  | 'CDM' | 'CM' | 'CAM' | 'LM' | 'RM'
  | 'LW' | 'RW' | 'CF' | 'ST'

// EA's `club_position` for the player (starting XI code, or SUB / RES)
export type EaPosition =
  | 'GK'
  | 'LWB' | 'LB' | 'LCB' | 'CB' | 'RCB' | 'RB' | 'RWB'
  | 'LDM' | 'CDM' | 'RDM' | 'LM' | 'LCM' | 'CM' | 'RCM' | 'RM' | 'LAM' | 'CAM' | 'RAM'
  | 'LW' | 'LF' | 'CF' | 'RF' | 'RW' | 'LS' | 'ST' | 'RS'
  | 'SUB' | 'RES'

export type Fit = 'natural' | 'adjacent'

export interface League {
  id: number
  name: string
}

export interface VersionInfo {
  id: number
  label: string
  snapshotDate: string
  leagues: League[]
  teamCount: number
}

export interface OutfieldStats {
  pac: number
  sho: number
  pas: number
  dri: number
  def: number
  phy: number
}

export interface GkStats {
  div: number
  han: number
  kic: number
  ref: number
  spd: number
  pos: number
}

interface PlayerBase {
  id: number
  name: string
  fullName: string
  nation: string
  // Flag code for flag-icons: ISO 3166-1 alpha-2, or gb-eng / gb-sct / gb-wls / gb-nir (D39)
  nationCode: string
  age: number
  positions: Position[]
  ovr: number
  eaPos: EaPosition
  fit: Fit
}

export interface GoalkeeperPlayer extends PlayerBase {
  slot: 'GK'
  gk: GkStats
  stats?: never
}

export interface OutfieldPlayer extends PlayerBase {
  slot: OutfieldSlot
  stats: OutfieldStats
  gk?: never
}

export type XiPlayer = GoalkeeperPlayer | OutfieldPlayer

export interface Team {
  id: number
  name: string
  leagueId: number
  ovr: number
  eaFormation: string
  xi: XiPlayer[]
}

export interface TeamsFile {
  version: number
  teams: Team[]
}

// One entry of index.json: every team across all versions, for the random matchup mode (D45)
export interface IndexEntry {
  v: number
  id: number
  name: string
  leagueId: number
  // Mean `ovr` of the Best XI, 2 decimals
  xiAvg: number
}
