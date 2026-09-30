import type { Slot, XiPlayer } from '../data/types'
import { placedResults, type GameState, type Side } from './game'
import type { GameSide } from './sides'

// A winner card that has been placed into its slot on the pitch
export interface PlacedCard {
  slot: Slot
  player: XiPlayer
  side: Side
  tie: boolean
  teamName: string
}

export function placedCards(state: GameState, sideA: GameSide, sideB: GameSide): PlacedCard[] {
  return placedResults(state).map((result) => {
    const round = state.rounds.find((r) => r.slot === result.slot)
    if (!round) throw new Error(`No round for slot ${result.slot}`)
    return {
      slot: result.slot,
      player: result.winner === 'A' ? round.a : round.b,
      side: result.winner,
      tie: result.tie,
      teamName: (result.winner === 'A' ? sideA : sideB).team.name,
    }
  })
}
