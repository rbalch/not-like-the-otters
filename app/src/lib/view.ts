export type View = 'wall' | 'decisions'

/**
 * Recognises a view key off `location.hash` — nothing more. Deliberately no
 * router — two screens don't need one, and deliberately no default: an
 * unrecognised hash (including `''`, on first launch or after something
 * resets it to empty) returns `null` rather than guessing, so the caller's
 * own default decides. That matters once T2/T8 write `location.hash = ''`
 * as "close and reset" — falling back to the caller's default instead of a
 * hardcoded screen is what keeps that closing action landing on the app's
 * actual default rather than on whichever screen this function happened to
 * prefer.
 *
 * Exact match only, on purpose: `'#Wall'` (wrong case), `'#wallet'` (prefix,
 * not the whole token) and `'#wall/'` / `'#wall?x=1'` (trailing junk) all
 * return `null`. A hash is an identifier here, not a path or a query string
 * to parse leniently — loosening the match would make a typo silently
 * resolve to a real view instead of falling back to the default, which is
 * the exact failure-open shape this function exists to avoid.
 */
export function viewFromHash(hash: string): View | null {
  if (hash === '#wall') return 'wall'
  if (hash === '#decisions') return 'decisions'
  return null
}
