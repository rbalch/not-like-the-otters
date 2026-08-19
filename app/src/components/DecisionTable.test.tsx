import { describe, expect, it, afterEach } from 'vitest'
import { cleanup, render, screen, within } from '@testing-library/react'
import DecisionTable from './DecisionTable'
import type { Decision } from '../lib/decisions'

afterEach(() => {
  cleanup()
})

function decision(overrides: Partial<Decision> = {}): Decision {
  return {
    id: 'DEC-0',
    title: 'Some rule',
    status: 'accepted',
    kind: 'positive',
    supersededBy: null,
    ...overrides,
  }
}

describe('DecisionTable', () => {
  it('renders an accessible table with one row per decision', () => {
    render(
      <DecisionTable
        decisions={[
          decision({ id: 'DEC-0' }),
          decision({
            id: 'DEC-1',
            status: 'superseded',
            supersededBy: 'DEC-2',
          }),
        ]}
      />,
    )

    const table = screen.getByRole('table')
    const rows = within(table).getAllByRole('row')
    // header row + 2 data rows
    expect(rows).toHaveLength(3)
  })

  it('renders an empty decisions array without crashing, keeping the head', () => {
    render(<DecisionTable decisions={[]} />)

    const table = screen.getByRole('table')
    expect(within(table).getAllByRole('row')).toHaveLength(1)
  })

  it('renders "accepted" status with the tag-accent class and its text', () => {
    render(<DecisionTable decisions={[decision({ status: 'accepted' })]} />)

    const tag = screen.getByText('accepted')
    expect(tag.className).toContain('tag')
    expect(tag.className).toContain('tag-accent')
  })

  it('renders "superseded" status with the tag-neutral class and its text', () => {
    render(<DecisionTable decisions={[decision({ status: 'superseded' })]} />)

    const tag = screen.getByText('superseded')
    expect(tag.className).toContain('tag')
    expect(tag.className).toContain('tag-neutral')
  })

  it('renders an unknown status (proposed) with the tag-outline fallback and its text', () => {
    render(<DecisionTable decisions={[decision({ status: 'proposed' })]} />)

    const tag = screen.getByText('proposed')
    expect(tag.className).toContain('tag')
    expect(tag.className).toContain('tag-outline')
  })

  it('renders an arbitrary unrecognised status verbatim with the fallback class, never blank', () => {
    render(<DecisionTable decisions={[decision({ status: 'wat' })]} />)

    const tag = screen.getByText('wat')
    expect(tag.className).toContain('tag-outline')
  })

  it('renders an empty superseded-by cell when supersededBy is null, not "null" or "undefined"', () => {
    render(
      <DecisionTable
        decisions={[decision({ id: 'DEC-0', supersededBy: null })]}
      />,
    )

    const table = screen.getByRole('table')
    const dataRow = within(table).getAllByRole('row')[1]
    const cells = within(dataRow).getAllByRole('cell')
    const supersededCell = cells[cells.length - 1]
    expect(supersededCell.textContent).toBe('')
    expect(supersededCell.textContent).not.toContain('null')
    expect(supersededCell.textContent).not.toContain('undefined')
  })

  it('surfaces a non-null supersededBy value in the superseded-by cell', () => {
    render(
      <DecisionTable
        decisions={[decision({ id: 'DEC-1', supersededBy: 'DEC-2' })]}
      />,
    )

    expect(screen.getByText('superseded by DEC-2')).toBeTruthy()
  })

  it('applies text-muted to the superseded-by cell', () => {
    render(
      <DecisionTable
        decisions={[decision({ id: 'DEC-1', supersededBy: 'DEC-2' })]}
      />,
    )

    const table = screen.getByRole('table')
    const dataRow = within(table).getAllByRole('row')[1]
    const cells = within(dataRow).getAllByRole('cell')
    const supersededCell = cells[cells.length - 1]
    expect(supersededCell.className).toContain('text-muted')
  })

  it('renders the id and title text for each decision', () => {
    render(
      <DecisionTable
        decisions={[decision({ id: 'DEC-7', title: 'A very specific rule' })]}
      />,
    )

    expect(screen.getByText('DEC-7')).toBeTruthy()
    expect(screen.getByText('A very specific rule')).toBeTruthy()
  })

  it('renders header cells with columnheader role, correct text, in order', () => {
    render(<DecisionTable decisions={[]} />)

    const table = screen.getByRole('table')
    const headers = within(table).getAllByRole('columnheader')
    expect(headers.map((h) => h.textContent)).toEqual([
      'ID',
      'Title',
      'Status',
      'Superseded by',
    ])
  })

  it("keeps each row's cells matched to its own decision, in input order", () => {
    render(
      <DecisionTable
        decisions={[
          decision({
            id: 'DEC-10',
            title: 'First rule',
            status: 'accepted',
            supersededBy: null,
          }),
          decision({
            id: 'DEC-11',
            title: 'Second rule',
            status: 'superseded',
            supersededBy: 'DEC-13',
          }),
          decision({
            id: 'DEC-12',
            title: 'Third rule',
            status: 'proposed',
            supersededBy: null,
          }),
        ]}
      />,
    )

    const table = screen.getByRole('table')
    const dataRows = within(table).getAllByRole('row').slice(1)
    expect(dataRows).toHaveLength(3)

    const expected = [
      {
        id: 'DEC-10',
        title: 'First rule',
        status: 'accepted',
        tagClass: 'tag-accent',
        superseded: '',
      },
      {
        id: 'DEC-11',
        title: 'Second rule',
        status: 'superseded',
        tagClass: 'tag-neutral',
        superseded: 'superseded by DEC-13',
      },
      {
        id: 'DEC-12',
        title: 'Third rule',
        status: 'proposed',
        tagClass: 'tag-outline',
        superseded: '',
      },
    ]

    dataRows.forEach((row, i) => {
      const cells = within(row).getAllByRole('cell')
      expect(cells).toHaveLength(4)

      const [idCell, titleCell, statusCell, supersededCell] = cells
      const exp = expected[i]

      expect(idCell.textContent).toBe(exp.id)
      expect(titleCell.textContent).toBe(exp.title)

      const tag = within(statusCell).getByText(exp.status)
      expect(tag.className).toContain('tag')
      expect(tag.className).toContain(exp.tagClass)

      expect(supersededCell.textContent).toBe(exp.superseded)
    })
  })
})
