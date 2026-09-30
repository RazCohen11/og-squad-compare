import type { Team, VersionInfo } from '../data/types'
import { ROUND_COUNT, SLOTS } from '../game/slots'
import styles from './GameScreen.module.css'
import { Pitch } from './Pitch'

interface Props {
  version: VersionInfo
  teamA: Team
  teamB: Team
  onBack: () => void
}

// Skeleton only: no guessing yet (stage 05). The first round is the GK slot (D8).
export function GameScreen({ version, teamA, teamB, onBack }: Props) {
  const round = 1
  const currentSlot = SLOTS[round - 1]

  return (
    <div className={styles.screen}>
      <header className={styles.header}>
        <button type="button" className={styles.back} onClick={onBack}>
          <span aria-hidden="true">←</span> Back
        </button>
        <div className={styles.titles}>
          <p className={styles.version}>{version.label}</p>
          <h1 className={styles.matchup}>
            <span className={styles.teamName}>{teamA.name}</span>
            <span className={styles.vs}>vs</span>
            <span className={styles.teamName}>{teamB.name}</span>
          </h1>
        </div>
      </header>

      <main className={styles.body}>
        <div className={styles.pitchArea}>
          <div className={styles.pitchFrame}>
            <Pitch currentSlot={currentSlot} />
          </div>
        </div>

        <section className={styles.guessArea} aria-label="Current round">
          <p className={styles.round}>
            <span className={styles.roundLabel}>Round</span>{' '}
            <span className={styles.roundValue}>
              {round} / {ROUND_COUNT}
            </span>
            <span className={styles.roundSlot}>{currentSlot}</span>
          </p>
          <div className={styles.cards}>
            <div className={styles.cardPlaceholder}>
              <span className={styles.cardTeam}>{teamA.name}</span>
              <span className={styles.cardHint}>Card</span>
            </div>
            <div className={styles.cardPlaceholder}>
              <span className={styles.cardTeam}>{teamB.name}</span>
              <span className={styles.cardHint}>Card</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
