import styles from './StatusMessage.module.css'

interface Props {
  kind: 'loading' | 'error'
  message: string
  onRetry?: () => void
  // Inline messages sit inside a screen; full-screen ones replace it
  inline?: boolean
}

export function StatusMessage({ kind, message, onRetry, inline = false }: Props) {
  return (
    <div
      className={`${styles.status} ${inline ? styles.inline : styles.fullScreen}`}
      role={kind === 'error' ? 'alert' : 'status'}
      aria-live="polite"
    >
      {kind === 'loading' && <span className={styles.spinner} aria-hidden="true" />}
      <p className={kind === 'error' ? styles.error : undefined}>{message}</p>
      {kind === 'error' && onRetry && (
        <button type="button" className={styles.retry} onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}
