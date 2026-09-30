// DOM helpers for animations. All of them respect `prefers-reduced-motion`.

export function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true
}

// Clones `source`, and flies the clone from the source's box into the target's box (shrinking it),
// then removes it. Resolves when done. Resolves immediately if motion is reduced or the API is missing.
export function flyInto(source: HTMLElement, target: HTMLElement, duration = 500): Promise<void> {
  if (prefersReducedMotion() || typeof source.animate !== 'function') return Promise.resolve()

  const from = source.getBoundingClientRect()
  const to = target.getBoundingClientRect()
  if (from.width === 0 || to.width === 0) return Promise.resolve()

  const clone = source.cloneNode(true) as HTMLElement
  clone.removeAttribute('data-face')
  clone.setAttribute('aria-hidden', 'true')
  clone.inert = true
  Object.assign(clone.style, {
    position: 'fixed',
    left: `${from.left}px`,
    top: `${from.top}px`,
    width: `${from.width}px`,
    height: `${from.height}px`,
    margin: '0',
    zIndex: '1000',
    pointerEvents: 'none',
    transformOrigin: 'top left',
    // The source is the back face of a flipped card; the clone must face forward
    transform: 'none',
    backfaceVisibility: 'visible',
  })
  document.body.appendChild(clone)

  const dx = to.left - from.left
  const dy = to.top - from.top
  const sx = to.width / from.width
  const sy = to.height / from.height
  const animation = clone.animate(
    [
      { transform: 'translate(0, 0) scale(1, 1)', opacity: 1 },
      { transform: `translate(${dx * 0.35}px, ${dy * 0.35 - 24}px) scale(${0.35 + sx * 0.65}, ${0.35 + sy * 0.65})`, opacity: 1, offset: 0.45 },
      { transform: `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`, opacity: 0.85 },
    ],
    { duration, easing: 'cubic-bezier(0.45, 0, 0.2, 1)', fill: 'forwards' },
  )
  const cleanup = () => clone.remove()
  return animation.finished.then(cleanup, cleanup)
}
