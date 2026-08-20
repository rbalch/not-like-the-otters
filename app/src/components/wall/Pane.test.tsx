import { describe, expect, it, afterEach } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import Pane from './Pane'

afterEach(() => {
  cleanup()
})

describe('Pane', () => {
  it("renders exactly the content it is given, never a neighbour's", () => {
    render(
      <>
        <Pane aria-label="left">
          <span>Left content</span>
        </Pane>
        <Pane aria-label="right">
          <span>Right content</span>
        </Pane>
      </>,
    )

    const left = screen.getByLabelText('left')
    const right = screen.getByLabelText('right')

    expect(left.textContent).toBe('Left content')
    expect(right.textContent).toBe('Right content')
  })

  it('keeps the shared "pane" class and appends the pane-specific class given', () => {
    render(
      <Pane aria-label="gate" className="wall-gate">
        x
      </Pane>,
    )

    const div = screen.getByLabelText('gate')
    expect(div.className.split(' ')).toEqual(
      expect.arrayContaining(['pane', 'wall-gate']),
    )
  })

  it('renders the shared class alone when no pane-specific class is given', () => {
    render(<Pane aria-label="bare">x</Pane>)

    const div = screen.getByLabelText('bare')
    expect(div.className).toBe('pane')
  })

  it('renders empty — no placeholder text — when given no children', () => {
    render(<Pane aria-label="empty" data-testid="empty-pane" />)

    const div = screen.getByTestId('empty-pane')
    expect(div.textContent).toBe('')
  })
})
