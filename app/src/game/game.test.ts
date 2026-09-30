import { describe, expect, it } from 'vitest'
import type { Slot, XiPlayer } from '../data/types'
import {
  correctAnswer,
  createGame,
  currentResult,
  currentRound,
  gameReducer,
  getScore,
  placedResults,
  roundNumber,
  type GameAction,
  type GameState,
  type Guess,
} from './game'
import { SLOTS } from './slots'

function player(slot: Slot, ovr: number, id: number): XiPlayer {
  const base = {
    id,
    name: `P${id}`,
    fullName: `Player ${id}`,
    nation: 'Nowhere',
    age: 25,
    positions: [],
    ovr,
    eaPos: 'SUB' as const,
    fit: 'natural' as const,
  }
  return slot === 'GK'
    ? { ...base, slot, gk: { div: 1, han: 1, kic: 1, ref: 1, spd: 1, pos: 1 } }
    : { ...base, slot, stats: { pac: 1, sho: 1, pas: 1, dri: 1, def: 1, phy: 1 } }
}

// Ratings per slot for A and B; ties at LCB and ST
const OVR_A = [85, 80, 82, 78, 77, 84, 83, 86, 88, 90, 79]
const OVR_B = [84, 81, 82, 79, 76, 84, 85, 80, 87, 90, 81]
// Correct answers per round, derived from the ratings above
const ANSWERS: Guess[] = ['A', 'B', 'equal', 'B', 'A', 'equal', 'B', 'A', 'A', 'equal', 'B']

function xi(ovrs: number[], idOffset: number): XiPlayer[] {
  // Deliberately reversed, so the game must look players up by slot, not by index
  return SLOTS.map((slot, i) => player(slot, ovrs[i], idOffset + i)).reverse()
}

function newGame(): GameState {
  return createGame(xi(OVR_A, 100), xi(OVR_B, 200))
}

function run(state: GameState, actions: GameAction[]): GameState {
  return actions.reduce(gameReducer, state)
}

function playAll(guesses: Guess[]): GameState {
  let state = newGame()
  for (const guess of guesses) {
    state = run(state, [{ type: 'guess', guess }, { type: 'next' }])
  }
  return state
}

describe('correctAnswer', () => {
  it('compares ovr', () => {
    expect(correctAnswer(player('ST', 90, 1), player('ST', 89, 2))).toBe('A')
    expect(correctAnswer(player('ST', 70, 1), player('ST', 89, 2))).toBe('B')
    expect(correctAnswer(player('ST', 89, 1), player('ST', 89, 2))).toBe('equal')
  })
})

describe('game flow', () => {
  it('starts in round 1 at GK, guessing', () => {
    const state = newGame()
    expect(state.phase).toBe('guessing')
    expect(roundNumber(state)).toBe(1)
    expect(currentRound(state)?.slot).toBe('GK')
  })

  it('plays the rounds in slot order (D8) and pairs players by slot', () => {
    let state = newGame()
    const seen: Slot[] = []
    for (let i = 0; i < 11; i++) {
      const round = currentRound(state)!
      seen.push(round.slot)
      expect(round.a.slot).toBe(round.slot)
      expect(round.b.slot).toBe(round.slot)
      state = run(state, [{ type: 'guess', guess: 'A' }, { type: 'next' }])
    }
    expect(seen).toEqual([...SLOTS])
  })

  it.each([
    ['A', 'A', true],
    ['B', 'A', false],
    ['equal', 'A', false],
  ] as const)('round with answer A: guess %s → correct %s', (guess, answer, correct) => {
    const state = run(newGame(), [{ type: 'guess', guess }])
    const result = currentResult(state)!
    expect(result.answer).toBe(answer)
    expect(result.correct).toBe(correct)
    expect(result.winner).toBe('A')
  })

  it.each([
    ['B', true],
    ['A', false],
    ['equal', false],
  ] as const)('round with answer B: guess %s → correct %s', (guess, correct) => {
    // Round 2 (LB): 80 vs 81
    const state = run(newGame(), [{ type: 'guess', guess: 'A' }, { type: 'next' }, { type: 'guess', guess }])
    const result = currentResult(state)!
    expect(result.slot).toBe('LB')
    expect(result.answer).toBe('B')
    expect(result.correct).toBe(correct)
    expect(result.winner).toBe('B')
  })

  it.each([
    ['equal', true],
    ['A', false],
    ['B', false],
  ] as const)('tie round: guess %s → correct %s, Team A placed with a tie flag (D32)', (guess, correct) => {
    // Round 3 (LCB): 82 vs 82
    let state = playAll(['A', 'B'])
    state = gameReducer(state, { type: 'guess', guess })
    const result = currentResult(state)!
    expect(result.slot).toBe('LCB')
    expect(result.answer).toBe('equal')
    expect(result.correct).toBe(correct)
    expect(result.tie).toBe(true)
    expect(result.winner).toBe('A')
  })

  it('places a revealed round on the pitch only after Next', () => {
    let state = gameReducer(newGame(), { type: 'guess', guess: 'A' })
    expect(state.phase).toBe('revealed')
    expect(placedResults(state)).toHaveLength(0)
    state = gameReducer(state, { type: 'next' })
    expect(placedResults(state).map((r) => r.slot)).toEqual(['GK'])
    expect(currentRound(state)?.slot).toBe('LB')
  })

  it('ignores actions that do not fit the phase', () => {
    const start = newGame()
    expect(gameReducer(start, { type: 'next' })).toBe(start)
    const revealed = gameReducer(start, { type: 'guess', guess: 'A' })
    expect(gameReducer(revealed, { type: 'guess', guess: 'B' })).toBe(revealed)
  })

  it('finishes after round 11 and ignores further actions', () => {
    let state = playAll(Array(10).fill('A'))
    expect(roundNumber(state)).toBe(11)
    expect(currentRound(state)?.slot).toBe('RW')
    state = run(state, [{ type: 'guess', guess: 'B' }, { type: 'next' }])
    expect(state.phase).toBe('finished')
    expect(state.results).toHaveLength(11)
    expect(currentRound(state)).toBeNull()
    expect(placedResults(state)).toHaveLength(11)
    expect(gameReducer(state, { type: 'guess', guess: 'A' })).toBe(state)
    expect(gameReducer(state, { type: 'next' })).toBe(state)
  })
})

describe('score', () => {
  it('derives correct/wrong and the slot tally', () => {
    const state = playAll(ANSWERS)
    expect(getScore(state)).toEqual({ correct: 11, wrong: 0, slotsA: 4, slotsB: 4, ties: 3 })

    const allA = playAll(Array(11).fill('A'))
    // Correct only where the answer is A (4 rounds); the slot tally does not depend on guesses
    expect(getScore(allA)).toEqual({ correct: 4, wrong: 7, slotsA: 4, slotsB: 4, ties: 3 })
  })

  it('counts a revealed round immediately', () => {
    const state = gameReducer(newGame(), { type: 'guess', guess: 'B' })
    expect(getScore(state)).toEqual({ correct: 0, wrong: 1, slotsA: 1, slotsB: 0, ties: 0 })
  })
})

describe('restart', () => {
  it('starts over with the same teams', () => {
    const finished = playAll(ANSWERS)
    const restarted = gameReducer(finished, { type: 'restart' })
    expect(restarted.phase).toBe('guessing')
    expect(restarted.roundIndex).toBe(0)
    expect(restarted.results).toEqual([])
    expect(restarted.rounds).toBe(finished.rounds)
    expect(getScore(restarted)).toEqual({ correct: 0, wrong: 0, slotsA: 0, slotsB: 0, ties: 0 })
  })
})
