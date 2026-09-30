import styles from './Footer.module.css'

// Disclaimer and data credit (D44), shown on the setup and end screens
export function Footer() {
  return (
    <footer className={styles.footer}>
      <p>Fan project — not affiliated with EA SPORTS.</p>
      <p>Ratings: SoFIFA data via Kaggle (EA Sports FC 24 complete player dataset).</p>
    </footer>
  )
}
