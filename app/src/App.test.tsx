import { describe, expect, it, vi, afterEach } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import App from './App'

const { invokeMock } = vi.hoisted(() => ({ invokeMock: vi.fn() }))

vi.mock('@tauri-apps/api/core', () => ({
  invoke: invokeMock,
}))

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})

describe('App', () => {
  it('renders the decisions the command returns, including a superseded one', async () => {
    invokeMock.mockResolvedValueOnce([
      {
        id: 'DEC-0',
        title: 'No generated file is named AGENTS.md',
        status: 'accepted',
        kind: 'negative',
        superseded_by: null,
      },
      {
        id: 'DEC-1',
        title: 'An old rule',
        status: 'superseded',
        kind: 'positive',
        superseded_by: 'DEC-2',
      },
    ])

    render(<App />)

    await waitFor(() => screen.getByText('DEC-0'))

    expect(invokeMock).toHaveBeenCalledWith('list_decisions')
    expect(screen.getByText('DEC-0')).toBeTruthy()
    expect(
      screen.getByText('No generated file is named AGENTS.md'),
    ).toBeTruthy()
    expect(screen.getByText('accepted')).toBeTruthy()
    expect(screen.getByText('DEC-1')).toBeTruthy()
    // A superseded decision must never look plainly accepted: the row must
    // surface what superseded it.
    expect(screen.getByText('superseded by DEC-2')).toBeTruthy()
  })

  it('shows a visible error naming what went wrong, never an empty list', async () => {
    invokeMock.mockRejectedValueOnce(
      'registry.json is not valid governance registry JSON: EOF',
    )

    render(<App />)

    const alert = await waitFor(() => screen.getByRole('alert'))

    expect(alert.textContent).toContain(
      'registry.json is not valid governance registry JSON: EOF',
    )
    expect(screen.queryByRole('table')).toBeNull()
  })
})
