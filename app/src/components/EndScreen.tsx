import type { GameState, Guess, Score } from '../game/game'
import type { PlacedCard } from '../game/placed'
import type { GameSide } from '../game/sides'
import { ROUND_COUNT } from '../game/slots'
import styles from './EndScreen.module.css'
import { Footer } from './Footer'
import { GameHeader } from './GameHeader'
import { Pitch } from './Pitch'

interface Props {
  state: GameState
  score: Score
  placed: PlacedCard[]
  sideA: GameSide
  sideB: GameSide
  onBack: () => void
  onPlayAgain: () => void
  onNewTeams: () => void
}

function guessLabel(guess: Guess): string {
  return guess === 'equal' ? '=' : guess
}

// End screen (D34): score, slot tally, the combined XI and a summary of the 11 rounds
export function EndScreen({ state, score, placed, sideA, sideB, onBack, onPlayAgain, onNewTeams }: Props) {
  return (
    <div className={styles.screen}>
      <GameHeader sideA={sideA} sideB={sideB} onBack={onBack} />

      <main className={styles.body}>
        <section className={styles.summary} aria-label="Result">
          <p className={styles.bigScore}>
            <strong>{score.correct}</strong> / {ROUND_COUNT} correct
          </p>
          <p className={styles.wrongLine}>✗ {score.wrong} wrong</p>
          <p className={styles.tally}>
            Slots won:{' '}
            <span className={styles.tallyTeam}>
              <span className={styles.dotA} aria-hidden="true" />
              {sideA.team.name} {score.slotsA}
            </span>
            <span className={styles.tallyTeam}>
              <span className={styles.dotB} aria-hidden="true" />
              {sideB.team.name} {score.slotsB}
            </span>
            {score.ties > 0 && (
              <span className={styles.tallyTeam}>
                Ties {score.ties}
              </span>
            )}
          </p>
          <div className={styles.actions}>
            <button type="button" className={styles.primary} onClick={onPlayAgain} autoFocus>
              Play again
            </button>
            <button type="button" className={styles.secondary} onClick={onNewTeams}>
              New teams
            </button>
          </div>
        </section>

        <div className={styles.pitchWrap}>
          <Pitch currentSlot={null} placed={placed} />
        </div>

        <section className={styles.rounds} aria-label="Rounds">
          <h2 className={styles.roundsTitle}>Rounds</h2>
          <ol className={styles.list}>
            <li className={`${styles.row} ${styles.headRow}`} aria-hidden="true">
              <span>Slot</span>
              <span className={styles.teamHead}>
                <span className={styles.dotA} />A
              </span>
              <span className={styles.teamHead}>
                <span className={styles.dotB} />B
              </span>
              <span className={styles.guessCol}>Guess</span>
            </li>
            {state.results.map((result, i) => {
              const round = state.rounds[i]
              const aWins = result.tie || result.winner === 'A'
              const bWins = result.tie || result.winner === 'B'
              return (
                <li key={result.slot} className={styles.row}>
                  <span className={styles.slot}>{result.slot}</span>
                  <span className={`${styles.player} ${aWins ? styles.higher : ''}`}>
                    <span className={styles.playerName}>{round.a.name}</span> <b>{round.a.ovr}</b>
                  </span>
                  <span className={`${styles.player} ${bWins ? styles.higher : ''}`}>
                    <span className={styles.playerName}>{round.b.name}</span> <b>{round.b.ovr}</b>
                  </span>
                  <span className={styles.guessCol}>
                    <span className="visually-hidden">Guess </span>
                    {guessLabel(result.guess)}{' '}
                    <span className={result.correct ? styles.correct : styles.wrong}>
                      {result.correct ? '✓' : '✗'}
                      <span className="visually-hidden">{result.correct ? ' correct' : ' wrong'}</span>
                    </span>
                  </span>
                </li>
              )
            })}
          </ol>
        </section>
      </main>
      <Footer />
    </div>
  )
}
