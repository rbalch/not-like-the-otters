interface KickerProps {
  /** The uppercase section label, e.g. "The gate", "Promotion". */
  label: string
  /** Optional right-aligned meta text, e.g. a count or a timestamp. */
  meta?: string
}

/**
 * A pane's section label: the uppercase kicker line, with optional
 * right-aligned meta text on the same baseline, followed by the 1px
 * `var(--color-divider)` rule that separates it from the pane's body. Four
 * of the five wall panes pass `meta`; the gate column's footer stat is the
 * one exception, so `meta` stays optional rather than required.
 */
export default function Kicker({ label, meta }: KickerProps) {
  return (
    <div className="kicker">
      <div className="kicker-row">
        <span className="kicker-label">{label}</span>
        {meta !== undefined && <span className="kicker-meta">{meta}</span>}
      </div>
      <div className="kicker-rule" />
    </div>
  )
}
