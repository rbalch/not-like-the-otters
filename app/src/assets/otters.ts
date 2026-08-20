import calmImage from './otter-green.png'
import alertImage from './otter-red.png'

/** One otter portrait: the image plus the alt text describing what it means. */
interface OtterVariant {
  src: string
  alt: string
}

/**
 * The ledger's status light: calm (green) is normal; alert (red) means a
 * finding reached three sightings and needs a human.
 *
 * `src` and `alt` are carried together, per key, deliberately — a `Record`
 * of this shape cannot add a new key without also supplying its `alt`, so
 * the two can never drift apart the way two independent literals could.
 * For a screen-reader user, the alt text IS the status light: it must say
 * what the image means, not just what it depicts.
 */
export const otters: Record<'calm' | 'alert', OtterVariant> = {
  calm: {
    src: calmImage,
    alt: 'Otter mascot, calm — nothing in the ledger needs attention',
  },
  alert: {
    src: alertImage,
    alt: 'Otter mascot, alert — a finding has reached three sightings and needs a human',
  },
}
