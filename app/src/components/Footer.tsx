import styles from './Footer.module.css'

// Disclaimer (D44) and data credit (D58), shown on the setup and end screens
export function Footer() {
  return (
    <footer className={styles.footer}>
      <p>Fan project — not affiliated with EA SPORTS.</p>
      <p>Ratings: SoFIFA and EA SPORTS FC ratings data, via public Kaggle datasets.</p>
    </footer>
  )
}
