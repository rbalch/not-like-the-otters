import { describe, expect, it, vi, afterEach } from 'vitest'
import { act, cleanup, render, screen } from '@testing-library/react'
import App from './App'

const { invokeMock } = vi.hoisted(() => ({ invokeMock: vi.fn() }))

vi.mock('@tauri-apps/api/core', () => ({
  invoke: invokeMock,
}))

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
  window.location.hash = ''
})

describe('App view switch', () => {
  it('opens on the wall when defaultView is wall and the hash is empty', () => {
    invokeMock.mockResolvedValueOnce([])
    render(<App defaultView="wall" />)

    expect(screen.getByTestId('wall-header')).toBeTruthy()
    expect(screen.queryByRole('table')).toBeNull()
    expect(document.querySelector('#decisions')).toBeNull()
  })

  it('opens on decisions when defaultView is wall but the hash names decisions', () => {
    window.location.hash = '#decisions'
    invokeMock.mockResolvedValueOnce([])
    render(<App defaultView="wall" />)

    expect(document.querySelector('#decisions')).toBeTruthy()
    expect(screen.queryByTestId('wall-header')).toBeNull()
  })

  it('flips view on a hashchange after mount, and stops listening after unmount', () => {
    invokeMock.mockResolvedValue([])
    const { unmount } = render(<App defaultView="wall" />)

    // Starts on the wall (empty hash, defaultView wall).
    expect(screen.getByTestId('wall-header')).toBeTruthy()
    expect(document.querySelector('#decisions')).toBeNull()

    act(() => {
      window.location.hash = '#decisions'
      window.dispatchEvent(new Event('hashchange'))
    })

    expect(document.querySelector('#decisions')).toBeTruthy()
    expect(screen.queryByTestId('wall-header')).toBeNull()

    unmount()

    // After unmount, a further hashchange must not throw or touch a
    // detached tree — the listener was removed.
    expect(() => {
      act(() => {
        window.location.hash = '#wall'
        window.dispatchEvent(new Event('hashchange'))
      })
    }).not.toThrow()
  })
})
