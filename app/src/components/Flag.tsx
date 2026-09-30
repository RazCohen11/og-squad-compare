import { flagUrl } from '../lib/flags'
import styles from './Flag.module.css'

interface Props {
  code: string
  nation: string
  // Show the nation name next to the flag; otherwise it is available as alt text and tooltip
  withName?: boolean
  className?: string
}

export function Flag({ code, nation, withName = false, className = '' }: Props) {
  const url = flagUrl(code)
  return (
    <span className={`${styles.wrap} ${className}`} title={nation}>
      {url ? (
        <img className={styles.flag} src={url} alt={withName ? '' : nation} loading="lazy" decoding="async" />
      ) : (
        <span className={styles.fallback} aria-hidden="true" />
      )}
      {withName ? <span className={styles.name}>{nation}</span> : !url && <span className="visually-hidden">{nation}</span>}
    </span>
  )
}
