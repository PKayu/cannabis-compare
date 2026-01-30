'use client'

import React, { useState } from 'react'

interface AgeGateProps {
  onVerify: () => void
}

export default function AgeGate({ onVerify }: AgeGateProps) {
  const [birthDate, setBirthDate] = useState('')
  const [accepted, setAccepted] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!birthDate) {
      setError('Please enter your date of birth')
      return
    }

    if (!accepted) {
      setError('You must confirm that you are 21 or older')
      return
    }

    const birth = new Date(birthDate)
    const today = new Date()
    let age = today.getFullYear() - birth.getFullYear()
    const monthDiff = today.getMonth() - birth.getMonth()

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--
    }

    if (age < 21) {
      setError('You must be 21 years or older to access this site.')
      return
    }

    localStorage.setItem('age_verified', 'true')
    onVerify()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-lg animate-modal-in">
        <div className="text-center mb-4">
          <span className="text-4xl" role="img" aria-label="Welcome">👋</span>
        </div>
        <h2 className="text-2xl font-bold mb-4 text-cannabis-700 text-center">Welcome! Let's verify your age</h2>

        <p className="text-gray-600 mb-6 text-sm leading-relaxed text-center">
          This site is only for individuals 21 years of age or older. We require age verification to access cannabis-related information and content.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Birth Date Input */}
          <div>
            <label htmlFor="birthDate" className="block text-sm font-medium text-gray-700 mb-2">
              Date of Birth
            </label>
            <input
              id="birthDate"
              type="date"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cannabis-500"
              required
            />
          </div>

          {/* Confirmation Checkbox */}
          <div className="flex items-start">
            <input
              id="confirm"
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              className="mt-1 h-4 w-4 text-cannabis-600 rounded cursor-pointer"
            />
            <label htmlFor="confirm" className="ml-3 text-sm text-gray-700">
              I confirm I am 21 years or older and have a valid Utah Medical Cannabis card
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-amber-50 border border-amber-200 rounded-md p-3 animate-shake">
              <p className="text-amber-700 text-sm flex items-center gap-2">
                <span role="img" aria-label="Alert">⚠️</span>
                {error}
              </p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!accepted || !birthDate}
            className="w-full px-4 py-2 bg-cannabis-600 text-white font-medium rounded-md hover:bg-cannabis-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Continue
          </button>
        </form>

        {/* Compliance Disclaimer */}
        <p className="text-xs text-gray-500 text-center mt-6 leading-relaxed border-t pt-4">
          This site is for informational purposes only. It does not sell, distribute, or promote controlled substances. Not affiliated with any dispensary or retailer.
        </p>
      </div>
    </div>
  )
}
