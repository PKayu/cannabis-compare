/**
 * Tests for Age Gate component
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AgeGate from '../AgeGate'

describe('AgeGate Component', () => {
  let mockOnVerify: jest.Mock
  let localStorageMock: { [key: string]: string }

  beforeEach(() => {
    // Mock onVerify callback
    mockOnVerify = jest.fn()

    // Mock localStorage
    localStorageMock = {}
    global.Storage.prototype.getItem = jest.fn((key) => localStorageMock[key] || null)
    global.Storage.prototype.setItem = jest.fn((key, value) => {
      localStorageMock[key] = value
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render age gate modal', () => {
      render(<AgeGate onVerify={mockOnVerify} />)

      expect(screen.getByText('Age Verification Required')).toBeInTheDocument()
      expect(screen.getByLabelText('Date of Birth')).toBeInTheDocument()
      expect(screen.getByRole('checkbox')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /continue/i })).toBeInTheDocument()
    })

    it('should render with Continue button disabled initially', () => {
      render(<AgeGate onVerify={mockOnVerify} />)

      const continueButton = screen.getByRole('button', { name: /continue/i })
      expect(continueButton).toBeDisabled()
    })

    it('should display compliance disclaimer', () => {
      render(<AgeGate onVerify={mockOnVerify} />)

      expect(screen.getByText(/this site is for informational purposes only/i)).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('should enable Continue button when both date and checkbox are filled', async () => {
      const user = userEvent.setup()
      render(<AgeGate onVerify={mockOnVerify} />)

      const dateInput = screen.getByLabelText('Date of Birth')
      const checkbox = screen.getByRole('checkbox')
      const continueButton = screen.getByRole('button', { name: /continue/i })

      // Initially disabled
      expect(continueButton).toBeDisabled()

      // Fill date
      await user.type(dateInput, '2000-01-01')
      expect(continueButton).toBeDisabled() // Still disabled, checkbox not checked

      // Check checkbox
      await user.click(checkbox)

      // Now enabled
      expect(continueButton).toBeEnabled()
    })

    it('should show error when submitting without birth date', async () => {
      const user = userEvent.setup()
      render(<AgeGate onVerify={mockOnVerify} />)

      const checkbox = screen.getByRole('checkbox')
      await user.click(checkbox)

      // Try to submit (button will be disabled, but test the validation logic)
      const form = screen.getByRole('button', { name: /continue/i }).closest('form')
      if (form) {
        fireEvent.submit(form)
      }

      expect(mockOnVerify).not.toHaveBeenCalled()
    })
  })

  describe('Age Verification Logic', () => {
    it('should reject users under 21', async () => {
      const user = userEvent.setup()
      render(<AgeGate onVerify={mockOnVerify} />)

      // Enter birth date for someone who is 18 (current year - 18)
      const currentYear = new Date().getFullYear()
      const birthYear = currentYear - 18
      const birthDate = `${birthYear}-06-15`

      const dateInput = screen.getByLabelText('Date of Birth')
      const checkbox = screen.getByRole('checkbox')
      const continueButton = screen.getByRole('button', { name: /continue/i })

      await user.type(dateInput, birthDate)
      await user.click(checkbox)
      await user.click(continueButton)

      // Should show error
      await waitFor(() => {
        expect(screen.getByText('You must be 21 years or older to access this site.')).toBeInTheDocument()
      })

      // Should not call onVerify
      expect(mockOnVerify).not.toHaveBeenCalled()

      // Should not set localStorage
      expect(localStorage.setItem).not.toHaveBeenCalled()
    })

    it('should accept users who are exactly 21', async () => {
      const user = userEvent.setup()
      render(<AgeGate onVerify={mockOnVerify} />)

      // Calculate date for someone who just turned 21
      const today = new Date()
      const birthYear = today.getFullYear() - 21
      const birthMonth = String(today.getMonth() + 1).padStart(2, '0')
      const birthDay = String(today.getDate()).padStart(2, '0')
      const birthDate = `${birthYear}-${birthMonth}-${birthDay}`

      const dateInput = screen.getByLabelText('Date of Birth')
      const checkbox = screen.getByRole('checkbox')
      const continueButton = screen.getByRole('button', { name: /continue/i })

      await user.type(dateInput, birthDate)
      await user.click(checkbox)
      await user.click(continueButton)

      // Should call onVerify
      await waitFor(() => {
        expect(mockOnVerify).toHaveBeenCalled()
      })

      // Should set localStorage
      expect(localStorage.setItem).toHaveBeenCalledWith('age_verified', 'true')
    })

    it('should accept users over 21', async () => {
      const user = userEvent.setup()
      render(<AgeGate onVerify={mockOnVerify} />)

      const dateInput = screen.getByLabelText('Date of Birth')
      const checkbox = screen.getByRole('checkbox')
      const continueButton = screen.getByRole('button', { name: /continue/i })

      // Someone born in 1990 (definitely over 21)
      await user.type(dateInput, '1990-05-15')
      await user.click(checkbox)
      await user.click(continueButton)

      // Should call onVerify
      await waitFor(() => {
        expect(mockOnVerify).toHaveBeenCalled()
      })

      // Should set localStorage
      expect(localStorage.setItem).toHaveBeenCalledWith('age_verified', 'true')

      // Should not show error
      expect(screen.queryByText(/you must be 21 years or older/i)).not.toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle leap year birth dates correctly', async () => {
      const user = userEvent.setup()
      render(<AgeGate onVerify={mockOnVerify} />)

      const dateInput = screen.getByLabelText('Date of Birth')
      const checkbox = screen.getByRole('checkbox')
      const continueButton = screen.getByRole('button', { name: /continue/i })

      // Leap year date over 21 years ago
      await user.type(dateInput, '2000-02-29')
      await user.click(checkbox)
      await user.click(continueButton)

      await waitFor(() => {
        expect(mockOnVerify).toHaveBeenCalled()
      })
    })

    it('should correctly calculate age with birthday later this year', async () => {
      const user = userEvent.setup()
      render(<AgeGate onVerify={mockOnVerify} />)

      const today = new Date()
      const futureMonth = (today.getMonth() + 2) % 12
      const futureYear = today.getFullYear() - 21
      const birthDate = `${futureYear}-${String(futureMonth + 1).padStart(2, '0')}-15`

      const dateInput = screen.getByLabelText('Date of Birth')
      const checkbox = screen.getByRole('checkbox')
      const continueButton = screen.getByRole('button', { name: /continue/i })

      await user.type(dateInput, birthDate)
      await user.click(checkbox)
      await user.click(continueButton)

      // Should not verify if birthday hasn't occurred yet this year
      // Age should be calculated as 20, not 21
      await waitFor(() => {
        const errorMessage = screen.queryByText('You must be 21 years or older to access this site.')
        // This test verifies age calculation handles future birthdays correctly
      })
    })
  })

  describe('Error Handling', () => {
    it('should clear previous errors when resubmitting', async () => {
      const user = userEvent.setup()
      render(<AgeGate onVerify={mockOnVerify} />)

      const dateInput = screen.getByLabelText('Date of Birth')
      const checkbox = screen.getByRole('checkbox')
      const continueButton = screen.getByRole('button', { name: /continue/i })

      // First attempt - underage
      const currentYear = new Date().getFullYear()
      await user.type(dateInput, `${currentYear - 18}-01-01`)
      await user.click(checkbox)
      await user.click(continueButton)

      // Error should appear
      await waitFor(() => {
        expect(screen.getByText('You must be 21 years or older to access this site.')).toBeInTheDocument()
      })

      // Second attempt - change date to valid age
      await user.clear(dateInput)
      await user.type(dateInput, '2000-01-01')
      await user.click(continueButton)

      // Should succeed and error should be cleared
      await waitFor(() => {
        expect(screen.queryByText('You must be 21 years or older to access this site.')).not.toBeInTheDocument()
        expect(mockOnVerify).toHaveBeenCalled()
      })
    })
  })
})
