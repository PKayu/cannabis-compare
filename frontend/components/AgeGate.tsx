'use client'

import React from 'react'

interface AgeGateProps {
  onVerify: () => void
}

export default function AgeGate({ onVerify }: AgeGateProps) {
  const handleConfirm = () => {
    localStorage.setItem('age_verified', 'true')
    onVerify()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-lg animate-modal-in">
        <div className="text-center mb-4">
          <span className="text-4xl" role="img" aria-label="Welcome">👋</span>
        </div>
        <h2 className="text-2xl font-bold mb-4 text-cannabis-700 text-center">Welcome!</h2>

        <p className="text-gray-600 mb-6 text-sm leading-relaxed text-center">
          This site is only for individuals 21 years of age or older. Please confirm your age to continue.
        </p>

        <div className="space-y-3">
          <button
            onClick={handleConfirm}
            className="w-full px-4 py-3 bg-cannabis-600 text-white font-medium rounded-md hover:bg-cannabis-700 transition-colors"
          >
            I am 21 or older — Enter
          </button>
          <button
            onClick={() => window.location.href = 'https://www.google.com'}
            className="w-full px-4 py-3 bg-gray-100 text-gray-700 font-medium rounded-md hover:bg-gray-200 transition-colors"
          >
            I am under 21 — Exit
          </button>
        </div>

        {/* Compliance Disclaimer */}
        <p className="text-xs text-gray-500 text-center mt-6 leading-relaxed border-t pt-4">
          This site is for informational purposes only. It does not sell, distribute, or promote controlled substances. Not affiliated with any dispensary or retailer.
        </p>
      </div>
    </div>
  )
}
