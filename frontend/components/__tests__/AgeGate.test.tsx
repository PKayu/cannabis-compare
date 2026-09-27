/**
 * Tests for the current confirmation-based age gate.
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AgeGate from '../AgeGate'

describe('AgeGate Component', () => {
  const mockOnVerify = jest.fn()

  beforeEach(() => {
    mockOnVerify.mockReset()
    jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => undefined)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('explains the age requirement and presents both choices', () => {
    render(<AgeGate onVerify={mockOnVerify} />)

    expect(screen.getByRole('heading', { name: 'Welcome!' })).toBeInTheDocument()
    expect(screen.getByText(/only for individuals 21 years of age or older/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /i am 21 or older/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /i am under 21/i })).toBeInTheDocument()
  })

  it('displays the compliance disclaimer', () => {
    render(<AgeGate onVerify={mockOnVerify} />)

    expect(screen.getByText(/this site is for informational purposes only/i)).toBeInTheDocument()
    expect(screen.getByText(/not affiliated with any dispensary or retailer/i)).toBeInTheDocument()
  })

  it('records confirmation and continues for an adult user', async () => {
    const user = userEvent.setup()
    render(<AgeGate onVerify={mockOnVerify} />)

    await user.click(screen.getByRole('button', { name: /i am 21 or older/i }))

    expect(localStorage.setItem).toHaveBeenCalledWith('age_verified', 'true')
    expect(mockOnVerify).toHaveBeenCalledTimes(1)
  })
})
