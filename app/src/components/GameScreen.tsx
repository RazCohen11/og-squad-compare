import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import {
  createGame,
  currentResult,
  currentRound,
  gameReducer,
  getScore,
  roundNumber,
  type Guess,
  type Score,
} from '../game/game'
import { placedCards } from '../game/placed'
import type { GameSide } from '../game/sides'
import { ROUND_COUNT } from '../game/slots'
import { flyInto } from '../lib/motion'
import { ConfirmDialog } from './ConfirmDialog'
import { EndScreen } from './EndScreen'
import { GameHeader } from './GameHeader'
import styles from './GameScreen.module.css'
import { GuessPanel } from './GuessPanel'
import { Pitch } from './Pitch'

interface Props {
  sideA: GameSide
  sideB: GameSide
  onBack: () => void
  onNewTeams: () => void
}

// Keyboard: Left / 1 = A, Right / 2 = B, E / = = Equal, Enter / Space = Next
const KEY_TO_GUESS: Record<string, Guess> = {
  ArrowLeft: 'A',
  '1': 'A',
  ArrowRight: 'B',
  '2': 'B',
  e: 'equal',
  E: 'equal',
  '=': 'equal',
}

export function GameScreen({ sideA, sideB, onBack, onNewTeams }: Props) {
  const [state, dispatch] = useReducer(gameReducer, null, () => createGame(sideA.team.xi, sideB.team.xi))
  const [flying, setFlying] = useState(false)
  const [peek, setPeek] = useState(false)
  const [confirmingBack, setConfirmingBack] = useState(false)
  const boardRef = useRef<HTMLElement>(null)
  const phase = state.phase

  const guess = useCallback((g: Guess) => {
    setPeek(false)
    dispatch({ type: 'guess', guess: g })
  }, [])

  // Next: the winner card flies into its slot, then the next round starts (D36)
  const next = useCallback(() => {
    if (flying || state.phase !== 'revealed') return
    const result = currentResult(state)
    const board = boardRef.current
    const source = board?.querySelector<HTMLElement>(`[data-card-side="${result?.winner}"] [data-face="back"]`)
    const target = board?.querySelector<HTMLElement>(`[data-slot="${result?.slot}"]`)
    setPeek(false)
    if (!source || !target) {
      dispatch({ type: 'next' })
      return
    }
    setFlying(true)
    void flyInto(source, target).then(() => {
      dispatch({ type: 'next' })
      setFlying(false)
    })
  }, [flying, state])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.altKey || e.ctrlKey || e.metaKey || flying || confirmingBack) return
      const tag = (e.target as HTMLElement | null)?.tagName
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return
      if (phase === 'guessing') {
        const g = KEY_TO_GUESS[e.key]
        if (g) {
          e.preventDefault()
          guess(g)
        }
      } else if (phase === 'revealed' && (e.key === 'Enter' || e.key === ' ')) {
        // A focused button handles Enter / Space itself; avoid a double "Next"
        if (tag === 'BUTTON') return
        e.preventDefault()
        next()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [phase, flying, confirmingBack, guess, next])

  const score = getScore(state)
  const placed = placedCards(state, sideA, sideB)

  if (phase === 'finished') {
    return (
      <EndScreen
        state={state}
        score={score}
        placed={placed}
        sideA={sideA}
        sideB={sideB}
        onBack={onBack}
        onPlayAgain={() => dispatch({ type: 'restart' })}
        onNewTeams={onNewTeams}
      />
    )
  }

  const round = currentRound(state)!
  const n = roundNumber(state)

  return (
    <div className={styles.screen}>
      {/* Leaving mid-game asks first (D41) */}
      <GameHeader sideA={sideA} sideB={sideB} onBack={() => setConfirmingBack(true)} />
      <Scoreboard score={score} roundNumber={n} slot={round.slot} />

      <main className={styles.body} ref={boardRef}>
        <div className={styles.pitchArea}>
          <div className={styles.pitchFrame}>
            <Pitch currentSlot={round.slot} placed={placed} />
          </div>
        </div>

        <GuessPanel
          // One panel per round: cards flip in place, and nothing (e.g. focus) carries over
          key={n}
          round={round}
          roundNumber={n}
          isLastRound={n === ROUND_COUNT}
          result={currentResult(state)}
          sideA={sideA}
          sideB={sideB}
          peek={peek}
          flying={flying}
          onGuess={guess}
          onNext={next}
          onTogglePeek={() => setPeek((p) => !p)}
        />
      </main>

      <ConfirmDialog
        open={confirmingBack}
        title="Leave this game?"
        message="Your progress in this game will be lost."
        cancelLabel="Keep playing"
        confirmLabel="Leave game"
        onCancel={() => setConfirmingBack(false)}
        onConfirm={() => {
          setConfirmingBack(false)
          onBack()
        }}
      />
    </div>
  )
}

function Scoreboard({ score, roundNumber, slot }: { score: Score; roundNumber: number; slot: string }) {
  return (
    <div className={styles.scoreboard}>
      <p className={styles.mainScore} aria-label={`${score.correct} correct, ${score.wrong} wrong`}>
        <span className={styles.correct}>✓ {score.correct}</span>
        <span className={styles.wrong}>✗ {score.wrong}</span>
      </p>
      <p className={styles.tally} aria-label={`Slots won: Team A ${score.slotsA}, Team B ${score.slotsB}, ties ${score.ties}`}>
        <span className={styles.dotA} aria-hidden="true" />
        {score.slotsA} – {score.slotsB}
        <span className={styles.dotB} aria-hidden="true" />
        {score.ties > 0 && <span className={styles.ties}>· {score.ties} tie{score.ties > 1 ? 's' : ''}</span>}
      </p>
      <p className={styles.round}>
        <span className={styles.roundWord}>Round </span>
        <strong>
          {roundNumber} / {ROUND_COUNT}
        </strong>{' '}
        <span className={styles.slotChip}>{slot}</span>
      </p>
    </div>
  )
}
