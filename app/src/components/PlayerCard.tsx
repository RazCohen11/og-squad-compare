import type { XiPlayer } from '../data/types'
import type { RoundResult } from '../game/game'
import { shortVersionLabel, type GameSide } from '../game/sides'
import { displayName, initials, tierFor } from '../lib/cards'
import { Flag } from './Flag'
import styles from './PlayerCard.module.css'

// One card component with three states (original design, D5):
// - hidden: neutral frame, no tier colour (D38), no rating or stats in the DOM (D31)
// - revealed: tier-coloured (D37), rating, slot and the six stats; flips over from the hidden face
// - mini: the small card placed into a pitch slot
type Props =
  | {
      state: 'hidden' | 'revealed'
      player: XiPlayer
      team: GameSide
      // Revealed only: marks Higher / Tie / Your pick
      result?: RoundResult
      // Hidden only: tapping the card guesses this side
      onGuess?: () => void
      // Keyboard hint on the hidden card, e.g. "← 1"
      shortcut?: string
    }
  | {
      state: 'mini'
      player: XiPlayer
      team: GameSide
      tie: boolean
    }

const OUTFIELD_STATS = [
  ['pac', 'PAC'],
  ['sho', 'SHO'],
  ['pas', 'PAS'],
  ['dri', 'DRI'],
  ['def', 'DEF'],
  ['phy', 'PHY'],
] as const

const GK_STATS = [
  ['div', 'DIV'],
  ['han', 'HAN'],
  ['kic', 'KIC'],
  ['ref', 'REF'],
  ['spd', 'SPD'],
  ['pos', 'POS'],
] as const

const TIER_CLASS = { gold: styles.gold, silver: styles.silver, bronze: styles.bronze }

function sideClass(team: GameSide): string {
  return team.side === 'A' ? styles.sideA : styles.sideB
}

export function PlayerCard(props: Props) {
  if (props.state === 'mini') return <MiniCard player={props.player} team={props.team} tie={props.tie} />

  const { state, player, team, result, onGuess, shortcut } = props
  const revealed = state === 'revealed'

  return (
    <div className={`${styles.scene} ${sideClass(team)}`} data-card-side={team.side}>
      <div className={`${styles.flipper} ${revealed ? styles.flipped : ''}`}>
        <button
          type="button"
          className={`${styles.face} ${styles.front} ${sideClass(team)}`}
          onClick={onGuess}
          disabled={revealed}
          inert={revealed}
        >
          <HiddenFace player={player} team={team} shortcut={shortcut} />
        </button>
        {/* The revealed face is only mounted after the guess, so the rating is never in the DOM before */}
        {revealed && (
          <div className={`${styles.face} ${styles.back} ${TIER_CLASS[tierFor(player.ovr)]} ${sideClass(team)} ${outcomeClass(result, team)}`} data-face="back">
            <RevealedFace player={player} team={team} result={result} />
          </div>
        )}
      </div>
    </div>
  )
}

function outcomeClass(result: RoundResult | undefined, team: GameSide): string {
  if (!result) return ''
  if (result.tie || result.winner === team.side) return styles.higher
  return styles.lower
}

function ClubLine({ team }: { team: GameSide }) {
  return (
    <span className={styles.club}>
      <span className={styles.teamDot} aria-hidden="true" />
      <span className={styles.clubName}>{team.team.name}</span>
      <span className={styles.version}>{shortVersionLabel(team.version)}</span>
    </span>
  )
}

function HiddenFace({ player, team, shortcut }: { player: XiPlayer; team: GameSide; shortcut?: string }) {
  return (
    <>
      <span className={styles.top}>
        <span className={styles.ratingSlot}>
          <span className={styles.question} aria-hidden="true">
            ?
          </span>
        </span>
        <span className={styles.avatar} aria-hidden="true">
          {initials(player.name)}
        </span>
      </span>
      <span className={styles.name}>{player.name}</span>
      <span className={styles.positions}>{player.positions.join(' · ')}</span>
      <Flag code={player.nationCode} nation={player.nation} withName className={styles.nation} />
      <ClubLine team={team} />
      <span className={styles.age}>{player.age} yrs</span>
      <span className={styles.hint}>
        Higher?
        {shortcut && <kbd className={styles.kbd}>{shortcut}</kbd>}
      </span>
    </>
  )
}

function RevealedFace({ player, team, result }: { player: XiPlayer; team: GameSide; result?: RoundResult }) {
  const isHigher = result ? !result.tie && result.winner === team.side : false
  const picked = result?.guess === team.side
  const stats =
    player.slot === 'GK'
      ? GK_STATS.map(([key, label]) => [label, player.gk[key]] as const)
      : OUTFIELD_STATS.map(([key, label]) => [label, player.stats[key]] as const)

  return (
    <>
      <span className={styles.top}>
        <span className={styles.ratingSlot}>
          <span className={styles.ovr} aria-label={`Rating ${player.ovr}`}>
            {player.ovr}
          </span>
          <span className={styles.slot}>{player.slot}</span>
        </span>
        <span className={styles.avatar} aria-hidden="true">
          {initials(player.name)}
        </span>
      </span>
      <span className={styles.name}>{player.name}</span>
      <span className={styles.meta}>
        <Flag code={player.nationCode} nation={player.nation} />
        <ClubLine team={team} />
      </span>
      {/* Own row, so badges never cover the avatar */}
      <span className={styles.badges}>
        {isHigher && <span className={styles.badgeHigher}>Higher</span>}
        {result?.tie && <span className={styles.badgeTie}>Tie</span>}
        {picked && <span className={styles.badgePick}>Your pick</span>}
      </span>
      <dl className={styles.stats}>
        {stats.map(([label, value]) => (
          <div key={label} className={styles.stat}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </>
  )
}

function MiniCard({ player, team, tie }: { player: XiPlayer; team: GameSide; tie: boolean }) {
  return (
    <div className={`${styles.mini} ${TIER_CLASS[tierFor(player.ovr)]} ${sideClass(team)}`}>
      <span className="visually-hidden">
        {player.slot}: {player.name}, {player.ovr}, {team.team.name}
        {tie ? ', tie' : ''}
      </span>
      <span className={styles.miniOvr} aria-hidden="true">
        {player.ovr}
      </span>
      <span className={styles.miniName} aria-hidden="true">
        {displayName(player.name)}
      </span>
      {tie && (
        <span className={styles.tieTag} aria-hidden="true">
          TIE
        </span>
      )}
    </div>
  )
}
