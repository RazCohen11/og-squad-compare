import type { XiPlayer } from '../data/types'
import type { RoundResult } from '../game/game'
import { shortVersionLabel, type GameSide } from '../game/sides'
import styles from './PlayerCard.module.css'

// Text-only card (stage 05). Stage 06 restyles it; keep the hidden / revealed split.
interface Props {
  player: XiPlayer
  side: GameSide
  state: 'hidden' | 'revealed'
  // Revealed state only: the round result, to mark the higher card / tie and the player's pick
  result?: RoundResult
  // Hidden state only: tapping the card guesses this side
  onGuess?: () => void
  // Keyboard hint shown on the hidden card, e.g. "← or 1"
  shortcut?: string
}

const OUTFIELD_LABELS = [
  ['pac', 'PAC'],
  ['sho', 'SHO'],
  ['pas', 'PAS'],
  ['dri', 'DRI'],
  ['def', 'DEF'],
  ['phy', 'PHY'],
] as const

const GK_LABELS = [
  ['div', 'DIV'],
  ['han', 'HAN'],
  ['kic', 'KIC'],
  ['ref', 'REF'],
  ['spd', 'SPD'],
  ['pos', 'POS'],
] as const

export function PlayerCard({ player, side, state, result, onGuess, shortcut }: Props) {
  const sideClass = side.side === 'A' ? styles.sideA : styles.sideB
  const identity = (
    <>
      <span className={styles.team}>
        <span className={styles.marker} aria-hidden="true" />
        <span className={styles.teamName}>{side.team.name}</span>
        <span className={styles.version}>{shortVersionLabel(side.version)}</span>
      </span>
      <span className={styles.name}>{player.name}</span>
      <span className={styles.positions}>{player.positions.join(' · ')}</span>
      <span className={styles.meta}>
        {player.nation} · {player.age} yrs
      </span>
    </>
  )

  if (state === 'hidden') {
    // Rating and stats are deliberately not rendered here (D31)
    return (
      <button type="button" className={`${styles.card} ${styles.hidden} ${sideClass}`} onClick={onGuess}>
        {identity}
        <span className={styles.guessHint}>
          Higher?
          {shortcut && <kbd className={styles.kbd}>{shortcut}</kbd>}
        </span>
      </button>
    )
  }

  const isWinner = result ? !result.tie && result.winner === side.side : false
  const picked = result?.guess === side.side
  return (
    <div
      className={`${styles.card} ${styles.revealed} ${sideClass} ${isWinner || result?.tie ? styles.winner : styles.loser}`}
    >
      <span className={styles.badges}>
        {isWinner && <span className={styles.badgeHigher}>Higher</span>}
        {result?.tie && <span className={styles.badgeTie}>Tie</span>}
        {picked && <span className={styles.badgePick}>Your pick</span>}
      </span>
      <span className={styles.ovr} aria-label={`Rating ${player.ovr}`}>
        {player.ovr}
      </span>
      {identity}
      <dl className={styles.stats}>
        {player.slot === 'GK'
          ? GK_LABELS.map(([key, label]) => (
              <div key={key} className={styles.stat}>
                <dt>{label}</dt>
                <dd>{player.gk[key]}</dd>
              </div>
            ))
          : OUTFIELD_LABELS.map(([key, label]) => (
              <div key={key} className={styles.stat}>
                <dt>{label}</dt>
                <dd>{player.stats[key]}</dd>
              </div>
            ))}
      </dl>
    </div>
  )
}
