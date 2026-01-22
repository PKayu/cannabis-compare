import React from 'react'

interface DealBadgeProps {
  msrp: number
  dealPrice?: number | null
  discountPercent?: number | null
  className?: string
}

export default function DealBadge({ msrp, dealPrice, discountPercent, className = '' }: DealBadgeProps) {
  // Only show if there's an actual deal
  if (!dealPrice || dealPrice >= msrp) {
    return (
      <div className={className}>
        <span className="text-lg font-bold text-gray-900">
          ${msrp.toFixed(2)}
        </span>
      </div>
    )
  }

  const savings = msrp - dealPrice
  const savingsPercent = discountPercent || ((savings / msrp) * 100)

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div>
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-green-600">
            ${dealPrice.toFixed(2)}
          </span>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
            {savingsPercent.toFixed(0)}% OFF
          </span>
        </div>
        <div className="text-sm text-gray-500 line-through">
          ${msrp.toFixed(2)}
        </div>
      </div>
    </div>
  )
}
