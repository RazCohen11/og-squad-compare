import type { Slot } from '../data/types'
import { SLOTS, SLOT_POSITIONS } from '../game/slots'
import styles from './Pitch.module.css'

interface Props {
  currentSlot: Slot | null
}

// Vertical pitch (D29) drawn with CSS: attack at the top, goalkeeper at the bottom
export function Pitch({ currentSlot }: Props) {
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

      <ol className={styles.slots} aria-label="Starting XI slots">
        {SLOTS.map((slot) => {
          const { x, y } = SLOT_POSITIONS[slot]
          const isCurrent = slot === currentSlot
          return (
            <li
              key={slot}
              className={`${styles.slot} ${isCurrent ? styles.current : ''}`}
              style={{ left: `${x}%`, top: `${y}%` }}
              aria-current={isCurrent ? 'step' : undefined}
            >
              <span className={styles.slotCode}>{slot}</span>
              {isCurrent && <span className="visually-hidden"> (current round)</span>}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
