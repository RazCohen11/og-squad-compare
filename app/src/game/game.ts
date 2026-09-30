// Pure game logic (no React). One game = 11 rounds in slot order (D8); each round compares
// Team A's and Team B's player in the same slot.

import type { Slot, XiPlayer } from '../data/types'
import { SLOTS } from './slots'

export type Side = 'A' | 'B'
// What the player guesses, and also the correct answer of a round (D7)
export type Guess = 'A' | 'B' | 'equal'
export type Phase = 'guessing' | 'revealed' | 'finished'

export interface Round {
  slot: Slot
  a: XiPlayer
  b: XiPlayer
}

export interface RoundResult {
  slot: Slot
  guess: Guess
  answer: Guess
  correct: boolean
  // Side whose player goes into the slot; on a tie that is Team A (D32)
  winner: Side
  tie: boolean
}

export interface GameState {
  rounds: Round[]
  roundIndex: number
  phase: Phase
  results: RoundResult[]
}

export type GameAction = { type: 'guess'; guess: Guess } | { type: 'next' } | { type: 'restart' }

export interface Score {
  correct: number
  wrong: number
  slotsA: number
  slotsB: number
  ties: number
}

function playerInSlot(xi: XiPlayer[], slot: Slot, team: string): XiPlayer {
  const player = xi.find((p) => p.slot === slot)
  if (!player) throw new Error(`${team} has no player in slot ${slot}`)
  return player
}

export function createGame(xiA: XiPlayer[], xiB: XiPlayer[]): GameState {
  return {
    rounds: SLOTS.map((slot) => ({
      slot,
      a: playerInSlot(xiA, slot, 'Team A'),
      b: playerInSlot(xiB, slot, 'Team B'),
    })),
    roundIndex: 0,
    phase: 'guessing',
    results: [],
  }
}

export function correctAnswer(a: XiPlayer, b: XiPlayer): Guess {
  if (a.ovr > b.ovr) return 'A'
  if (b.ovr > a.ovr) return 'B'
  return 'equal'
}

export function resolveRound(round: Round, guess: Guess): RoundResult {
  const answer = correctAnswer(round.a, round.b)
  return {
    slot: round.slot,
    guess,
    answer,
    correct: guess === answer,
    winner: answer === 'B' ? 'B' : 'A',
    tie: answer === 'equal',
  }
}

export function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'guess': {
      if (state.phase !== 'guessing') return state
      const result = resolveRound(state.rounds[state.roundIndex], action.guess)
      return { ...state, phase: 'revealed', results: [...state.results, result] }
    }
    case 'next': {
      if (state.phase !== 'revealed') return state
      const last = state.roundIndex === state.rounds.length - 1
      return last
        ? { ...state, phase: 'finished' }
        : { ...state, phase: 'guessing', roundIndex: state.roundIndex + 1 }
    }
    case 'restart':
      return { ...state, roundIndex: 0, phase: 'guessing', results: [] }
  }
}

export function currentRound(state: GameState): Round | null {
  return state.phase === 'finished' ? null : state.rounds[state.roundIndex]
}

// Result of the round currently on screen, once it has been guessed
export function currentResult(state: GameState): RoundResult | null {
  return state.phase === 'revealed' ? state.results[state.roundIndex] : null
}

// Results whose winner is already placed on the pitch: a revealed round is placed only after "Next"
export function placedResults(state: GameState): RoundResult[] {
  return state.phase === 'revealed' ? state.results.slice(0, -1) : state.results
}

export function getScore(state: GameState): Score {
  const score: Score = { correct: 0, wrong: 0, slotsA: 0, slotsB: 0, ties: 0 }
  for (const r of state.results) {
    if (r.correct) score.correct++
    else score.wrong++
    if (r.tie) score.ties++
    else if (r.winner === 'A') score.slotsA++
    else score.slotsB++
  }
  return score
}

export function roundNumber(state: GameState): number {
  return Math.min(state.roundIndex + 1, state.rounds.length)
}
