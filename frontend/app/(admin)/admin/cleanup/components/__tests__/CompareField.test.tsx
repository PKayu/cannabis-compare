import React from 'react'
import { render, screen } from '@testing-library/react'
import { CompareField } from '../CompareField'

describe('CompareField', () => {
  it('highlights green when values match (case/whitespace insensitive)', () => {
    const { container } = render(
      <CompareField label="Type" scraped=" Flower " matched="flower" />
    )
    expect(container.firstChild).toHaveClass('bg-green-50')
    expect(screen.getByText('flower')).toBeInTheDocument()
  })

  it('highlights yellow when values differ', () => {
    const { container } = render(
      <CompareField label="Type" scraped="flower" matched="edible" />
    )
    expect(container.firstChild).toHaveClass('bg-yellow-50')
  })

  it('no highlight and N/A when both sides empty', () => {
    const { container } = render(<CompareField label="THC" scraped="" matched="" />)
    expect(container.firstChild).not.toHaveClass('bg-green-50')
    expect(container.firstChild).not.toHaveClass('bg-yellow-50')
    expect(screen.getByText('N/A')).toBeInTheDocument()
  })
})
