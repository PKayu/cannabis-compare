'use client'

import React, { useState, useEffect } from 'react'
import AgeGate from '@/components/AgeGate'

interface AgeGateWrapperProps {
  children: React.ReactNode
}

/**
 * Age Gate Wrapper Component
 *
 * Wraps the entire application and shows the age gate modal
 * on first visit until the user verifies they are 21+
 */
export default function AgeGateWrapper({ children }: AgeGateWrapperProps) {
  const [isVerified, setIsVerified] = useState(false)
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    // Only run on client side
    setIsClient(true)

    // Check if user has already verified their age
    const verified = localStorage.getItem('age_verified') === 'true'
    setIsVerified(verified)
  }, [])

  // Don't show age gate on server side
  if (!isClient) {
    return <>{children}</>
  }

  const handleVerify = () => {
    setIsVerified(true)
  }

  // Show age gate if not verified
  if (!isVerified) {
    return <AgeGate onVerify={handleVerify} />
  }

  return <>{children}</>
}
