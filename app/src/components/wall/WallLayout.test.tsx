import { describe, expect, it, afterEach } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import WallLayout from './WallLayout'

afterEach(() => {
  cleanup()
})

describe('WallLayout', () => {
  it("renders each slot's content in its own named region, never swapped", () => {
    render(
      <WallLayout
        rail={<span>RAIL-MARK</span>}
        gate={<span>GATE-MARK</span>}
        run={<span>RUN-MARK</span>}
        promotion={<span>PROMOTION-MARK</span>}
        milestone={<span>MILESTONE-MARK</span>}
      />,
    )

    expect(screen.getByTestId('wall-rail').textContent).toBe('RAIL-MARK')
    expect(screen.getByTestId('wall-gate').textContent).toBe('GATE-MARK')
    expect(screen.getByTestId('wall-run').textContent).toBe('RUN-MARK')
    expect(screen.getByTestId('wall-promotion').textContent).toBe(
      'PROMOTION-MARK',
    )
    expect(screen.getByTestId('wall-milestone').textContent).toBe(
      'MILESTONE-MARK',
    )
  })

  it('renders the rail slot even with no icons wired — T2 fills it in', () => {
    render(<WallLayout />)

    const rail = screen.getByTestId('wall-rail')
    expect(rail).toBeTruthy()
    expect(rail.textContent).toBe('')
  })

  it('shows the app name, the status text and the hint text in the header', () => {
    render(
      <WallLayout
        status="dev · static"
        hint="click a pane to peek · esc closes"
      />,
    )

    const header = screen.getByTestId('wall-header')
    expect(header.textContent).toBe(
      'The walldev · staticclick a pane to peek · esc closes',
    )
  })

  it('defaults the header status and hint text when none is given', () => {
    render(<WallLayout />)

    const header = screen.getByTestId('wall-header')
    expect(header.textContent).toContain('dev · static')
    expect(header.textContent).toContain('click a pane to peek · esc closes')
  })

  it('nests the right-hand panes so the run band sits above the promotion/milestone split', () => {
    const { container } = render(
      <WallLayout
        gate={<span>G</span>}
        run={<span>R</span>}
        promotion={<span>P</span>}
        milestone={<span>M</span>}
      />,
    )

    const grid = container.querySelector('.wall-grid')
    const right = container.querySelector('.wall-right')
    const bottom = container.querySelector('.wall-bottom')
    const gate = screen.getByTestId('wall-gate')
    const run = screen.getByTestId('wall-run')
    const promotion = screen.getByTestId('wall-promotion')
    const milestone = screen.getByTestId('wall-milestone')

    expect(grid).toBeTruthy()
    expect(right).toBeTruthy()
    expect(bottom).toBeTruthy()

    // The gate column sits directly in the outer grid — the narrow 268px
    // column, not nested inside either right-hand split.
    expect(gate.parentElement).toBe(grid)

    // The run band sits directly in the right-hand grid, one level above
    // the bottom split, not inside it.
    expect(run.parentElement).toBe(right)
    expect(bottom?.contains(run)).toBe(false)

    // Promotion and milestone sit inside the bottom split, not the run row.
    expect(bottom?.contains(promotion)).toBe(true)
    expect(bottom?.contains(milestone)).toBe(true)
    expect(right?.contains(bottom)).toBe(true)
  })
})
