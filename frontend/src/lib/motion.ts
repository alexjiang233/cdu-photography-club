/** Shared preference for CSS, WAAPI and gesture momentum. */
export function reducedMotion() {
  return (
    typeof window !== 'undefined' &&
    (window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
      document.documentElement.dataset.motion === 'reduced')
  );
}
