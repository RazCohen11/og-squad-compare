import { shortVersionLabel, type GameSide } from '../game/sides'
import styles from './GameHeader.module.css'

interface Props {
  sideA: GameSide
  sideB: GameSide
  onBack: () => void
}

export function GameHeader({ sideA, sideB, onBack }: Props) {
  return (
    <header className={styles.header}>
      <button type="button" className={styles.back} onClick={onBack}>
        <span aria-hidden="true">←</span> Back
      </button>
      <h1 className={styles.matchup}>
        <TeamName side={sideA} />
        <span className={styles.vs}>vs</span>
        <TeamName side={sideB} />
      </h1>
    </header>
  )
}

function TeamName({ side }: { side: GameSide }) {
  return (
    <span className={`${styles.team} ${side.side === 'A' ? styles.sideA : styles.sideB}`}>
      <span className={styles.marker} aria-hidden="true" />
      <span className={styles.name}>{side.team.name}</span>
      <span className={styles.version}>· {shortVersionLabel(side.version)}</span>
    </span>
  )
}
