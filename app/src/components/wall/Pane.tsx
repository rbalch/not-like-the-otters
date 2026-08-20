import type { ReactNode } from 'react'

interface PaneProps {
  children?: ReactNode
  /** Extra class appended after the shared `pane` class, e.g. `wall-gate`. */
  className?: string
  'aria-label'?: string
  'data-testid'?: string
}

/**
 * The wall's shared pane box: `background: var(--color-bg)` over the content
 * grid's `--color-divider` background, plus the grid's 1px `gap`, is what
 * draws the hairlines between panes. A pane must never draw its own border —
 * that would double the line (or draw the wrong colour once `#4b`'s gate-red
 * state exists) instead of letting the grid gutter show through.
 */
export default function Pane({ children, className = '', ...rest }: PaneProps) {
  return (
    <div className={['pane', className].filter(Boolean).join(' ')} {...rest}>
      {children}
    </div>
  )
}
