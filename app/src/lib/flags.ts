// Flag image URLs from the locally bundled flag-icons package (D39, MIT). Each SVG is emitted as its
// own asset (see vite.config.ts), so a flag is only downloaded when it is shown.
const FLAG_URLS = import.meta.glob<string>('/node_modules/flag-icons/flags/4x3/*.svg', {
  query: '?url',
  import: 'default',
  eager: true,
})

export function flagUrl(code: string): string | null {
  return FLAG_URLS[`/node_modules/flag-icons/flags/4x3/${code}.svg`] ?? null
}

export function flagCount(): number {
  return Object.keys(FLAG_URLS).length
}
