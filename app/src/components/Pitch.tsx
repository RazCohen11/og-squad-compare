import type { Slot } from '../data/types'
import type { PlacedCard } from '../game/placed'
import { SLOTS, SLOT_POSITIONS } from '../game/slots'
import styles from './Pitch.module.css'
import { PlayerCard } from './PlayerCard'

interface Props {
  currentSlot: Slot | null
  placed: PlacedCard[]
}

// Vertical pitch (D29) drawn with CSS: attack at the top, goalkeeper at the bottom
export function Pitch({ currentSlot, placed }: Props) {
  const bySlot = new Map(placed.map((card) => [card.slot, card]))

  return (
    <div className={styles.pitch}>
      <div className={styles.markings} aria-hidden="true">
        <div className={styles.outline} />
        <div className={styles.halfway} />
        <div className={styles.centreCircle} />
        <div className={styles.centreSpot} />
        <div className={`${styles.penaltyBox} ${styles.top}`} />
        <div className={`${styles.goalBox} ${styles.top}`} />
        <div className={`${styles.penaltyBox} ${styles.bottom}`} />
        <div className={`${styles.goalBox} ${styles.bottom}`} />
      </div>

      <ol className={styles.slots} aria-label="Combined XI">
        {SLOTS.map((slot) => {
          const { x, y } = SLOT_POSITIONS[slot]
          const isCurrent = slot === currentSlot
          const card = bySlot.get(slot)
          return (
            <li
              key={slot}
              className={`${styles.slot} ${isCurrent ? styles.current : ''} ${card ? styles.filled : ''}`}
              style={{ left: `${x}%`, top: `${y}%` }}
              aria-current={isCurrent ? 'step' : undefined}
              // Target of the "fly to slot" animation
              data-slot={slot}
            >
              {card ? (
                <PlayerCard state="mini" player={card.player} team={card.team} tie={card.tie} />
              ) : (
                <>
                  <span className={styles.slotCode}>{slot}</span>
                  {isCurrent && <span className="visually-hidden"> (current round)</span>}
                </>
              )}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
