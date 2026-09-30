import type { Guess, Round, RoundResult } from '../game/game'
import type { GameSide } from '../game/sides'
import styles from './GuessPanel.module.css'
import { PlayerCard } from './PlayerCard'

interface Props {
  round: Round
  roundNumber: number
  isLastRound: boolean
  // Null while guessing, set once the round is revealed
  result: RoundResult | null
  sideA: GameSide
  sideB: GameSide
  // Phones: the panel is collapsed so the pitch is visible
  peek: boolean
  // The winner card is flying to its slot: the panel steps aside
  flying: boolean
  onGuess: (guess: Guess) => void
  onNext: () => void
  onTogglePeek: () => void
}

// On phones an overlay over the dimmed pitch, on desktop a panel next to it (D35).
// Mounted once per round (keyed by the parent), so the cards flip in place on reveal.
export function GuessPanel(props: Props) {
  const { round, roundNumber, isLastRound, result, sideA, sideB, peek, flying, onGuess, onNext, onTogglePeek } = props
  const revealed = result !== null
  const cardState = revealed ? 'revealed' : 'hidden'
  const classes = [styles.overlay, peek ? styles.peek : '', flying ? styles.flying : ''].join(' ')

  return (
    <section className={classes} aria-label={`Round ${roundNumber}, slot ${round.slot}`} inert={flying}>
      <div className={styles.panel} inert={peek}>
        <div className={styles.questionRow}>
          <p className={styles.question}>
            <span className={styles.slot}>{round.slot}</span>
            {revealed ? <ResultLine result={result} round={round} sideA={sideA} sideB={sideB} /> : 'Who had the higher rating?'}
          </p>
          <button type="button" className={styles.peekButton} onClick={onTogglePeek} aria-expanded={!peek}>
            <PitchIcon />
            <span>Pitch</span>
          </button>
        </div>

        <div className={styles.cards}>
          <PlayerCard
            state={cardState}
            player={round.a}
            team={sideA}
            result={result ?? undefined}
            onGuess={() => onGuess('A')}
            shortcut="← 1"
          />
          <PlayerCard
            state={cardState}
            player={round.b}
            team={sideB}
            result={result ?? undefined}
            onGuess={() => onGuess('B')}
            shortcut="→ 2"
          />
        </div>

        {revealed ? (
          // Focus moves here after a guess, so Enter / Space continues. Distinct keys keep React from
          // reusing this DOM node as the Equal button, which would carry the focus into the next round.
          <button key="next" type="button" className={styles.next} onClick={onNext} autoFocus>
            {isLastRound ? 'See results' : 'Next'} <span aria-hidden="true">→</span>
          </button>
        ) : (
          <button key="equal" type="button" className={styles.equal} onClick={() => onGuess('equal')}>
            = Equal
            <kbd className={styles.kbd}>E</kbd>
          </button>
        )}
      </div>

      {/* Phones only: brings the collapsed panel back */}
      {peek && (
        <button type="button" className={styles.showCards} onClick={onTogglePeek} autoFocus>
          <span aria-hidden="true">▲</span> Show cards
        </button>
      )}
    </section>
  )
}

function PitchIcon() {
  return (
    <svg className={styles.icon} viewBox="0 0 16 20" aria-hidden="true">
      <rect x="1" y="1" width="14" height="18" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <line x1="1" y1="10" x2="15" y2="10" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="8" cy="10" r="2.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function ResultLine({ result, round, sideA, sideB }: { result: RoundResult; round: Round; sideA: GameSide; sideB: GameSide }) {
  let detail: string
  if (result.tie) detail = `Both ${round.a.ovr}: it's a tie.`
  else {
    const winner = result.winner === 'A' ? sideA : sideB
    const high = Math.max(round.a.ovr, round.b.ovr)
    const low = Math.min(round.a.ovr, round.b.ovr)
    detail = `${winner.team.name} higher, ${high} vs ${low}.`
  }
  return (
    <span className={styles.result} role="status">
      <strong className={result.correct ? styles.correct : styles.wrong}>
        {result.correct ? '✓ Correct' : '✗ Wrong'}
      </strong>{' '}
      <span className={styles.detail}>{detail}</span>
    </span>
  )
}
