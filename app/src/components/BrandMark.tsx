import { otters } from '../assets/otters'

interface BrandMarkProps {
  /** Which otter to show. M1 flips this key; M2 only ever passes 'calm'. */
  otter?: keyof typeof otters
}

/**
 * The window's brand mark — the ledger's status light. Defaults to the calm
 * (green) otter; M1's job is passing `otter="alert"` when a finding needs a
 * human. `src` and `alt` come from the same map entry so they can never
 * describe two different otters. See
 * `docs/milestones/M2-claude-design-ingest.md`.
 */
function BrandMark({ otter = 'calm' }: BrandMarkProps) {
  const { src, alt } = otters[otter]

  return (
    <img className="brand-mark" src={src} alt={alt} width={128} height={128} />
  )
}

export default BrandMark
