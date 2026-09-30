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
  onGuess: (guess: Guess) => void
  onNext: () => void
}

// On phones an overlay over the dimmed pitch, on desktop a panel next to it (D35)
export function GuessPanel({ round, roundNumber, isLastRound, result, sideA, sideB, onGuess, onNext }: Props) {
  const revealed = result !== null
  const cardState = revealed ? 'revealed' : 'hidden'

  return (
    <section className={styles.overlay} aria-label={`Round ${roundNumber}, slot ${round.slot}`}>
      <div className={styles.panel}>
        <p className={styles.question}>
          <span className={styles.slot}>{round.slot}</span>
          {revealed ? <ResultLine result={result} round={round} sideA={sideA} sideB={sideB} /> : 'Who had the higher rating?'}
        </p>

        <div className={styles.cards}>
          <PlayerCard
            key={`a-${roundNumber}-${cardState}`}
            player={round.a}
            side={sideA}
            state={cardState}
            result={result ?? undefined}
            onGuess={() => onGuess('A')}
            shortcut="← 1"
          />
          <PlayerCard
            key={`b-${roundNumber}-${cardState}`}
            player={round.b}
            side={sideB}
            state={cardState}
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
    </section>
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
