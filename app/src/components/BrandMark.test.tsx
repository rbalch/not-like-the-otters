import { describe, expect, it, afterEach } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import BrandMark from './BrandMark'
import { otters } from '../assets/otters'

afterEach(() => {
  cleanup()
})

describe('BrandMark', () => {
  it('defaults to the calm (green) otter, with its own alt text', () => {
    render(<BrandMark />)

    const img = screen.getByRole('img') as HTMLImageElement
    expect(img.src).toContain(otters.calm.src)
    expect(img.src).not.toContain(otters.alert.src)
    expect(img.getAttribute('alt')).toBe(otters.calm.alt)
  })

  it('renders the alert (red) otter, with its own alt text, when told to', () => {
    render(<BrandMark otter="alert" />)

    const img = screen.getByRole('img') as HTMLImageElement
    expect(img.src).toContain(otters.alert.src)
    expect(img.src).not.toContain(otters.calm.src)
    expect(img.getAttribute('alt')).toBe(otters.alert.alt)
  })

  it("never renders one otter's image with the other's alt text", () => {
    render(<BrandMark otter="alert" />)

    const img = screen.getByRole('img') as HTMLImageElement
    expect(img.getAttribute('alt')).not.toBe(otters.calm.alt)
  })
})
