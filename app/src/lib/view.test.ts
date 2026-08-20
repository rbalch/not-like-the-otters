import { describe, expect, it } from 'vitest'
import { viewFromHash } from './view'

describe('viewFromHash', () => {
  it('recognises the two real views', () => {
    expect(viewFromHash('#wall')).toBe('wall')
    expect(viewFromHash('#decisions')).toBe('decisions')
  })

  it('falls back to null — not a guessed view — for anything else', () => {
    // Empty and bare `#`: no view named at all.
    expect(viewFromHash('')).toBeNull()
    expect(viewFromHash('#')).toBeNull()
    // Wrong case: a hash is an identifier here, not parsed case-insensitively.
    expect(viewFromHash('#Wall')).toBeNull()
    // A prefix of a real view name is not the view itself.
    expect(viewFromHash('#wallet')).toBeNull()
    // Trailing query-like or path-like junk: exact match only, no parsing.
    expect(viewFromHash('#wall?x=1')).toBeNull()
    expect(viewFromHash('#wall/')).toBeNull()
  })
})
