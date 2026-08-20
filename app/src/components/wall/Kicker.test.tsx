import { describe, expect, it, afterEach } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import Kicker from './Kicker'

afterEach(() => {
  cleanup()
})

describe('Kicker', () => {
  it('renders the label and the right-aligned meta text when given', () => {
    render(<Kicker label="The gate" meta="make check · 12.4s" />)

    expect(screen.getByText('The gate')).toBeTruthy()
    expect(screen.getByText('make check · 12.4s')).toBeTruthy()
  })

  it('omits the meta element entirely when no meta is given', () => {
    const { container } = render(<Kicker label="Milestone" />)

    expect(screen.getByText('Milestone')).toBeTruthy()
    expect(container.querySelector('.kicker-meta')).toBeNull()
  })

  it('always renders the divider rule beneath the label, with or without meta', () => {
    const { container: withMeta } = render(
      <Kicker label="Promotion" meta="bin 2 · 9 open" />,
    )
    expect(withMeta.querySelector('.kicker-rule')).toBeTruthy()
    cleanup()

    const { container: withoutMeta } = render(<Kicker label="Promotion" />)
    expect(withoutMeta.querySelector('.kicker-rule')).toBeTruthy()
  })

  it("never lets one Kicker's label or meta bleed into another's", () => {
    const { container } = render(
      <>
        <Kicker label="The run" meta="reviewer · pass 2" />
        <Kicker label="Promotion" meta="bin 2 · 9 open" />
      </>,
    )

    const rows = container.querySelectorAll('.kicker-row')
    expect(rows).toHaveLength(2)
    expect(rows[0].textContent).toBe('The runreviewer · pass 2')
    expect(rows[1].textContent).toBe('Promotionbin 2 · 9 open')
  })
})
