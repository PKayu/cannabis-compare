import React from 'react'

interface DealBadgeProps {
  msrp: number
  dealPrice?: number | null
  discountPercent?: number | null
  className?: string
}

export default function DealBadge({ msrp, dealPrice, discountPercent, className = '' }: DealBadgeProps) {
  if (!dealPrice || dealPrice >= msrp) {
    return (
      <div className={className}>
        <span className="font-display font-bold text-lg text-groovy-ink">
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
          <span className="font-display font-bold text-lg text-groovy-teal">
            ${dealPrice.toFixed(2)}
          </span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-display font-bold bg-groovy-sun text-groovy-ink border-2 border-groovy-ink shadow-[2px_2px_0px_#1C1917]">
            {savingsPercent.toFixed(0)}% OFF
          </span>
        </div>
        <div className="text-sm text-stone-400 line-through font-body">
          ${msrp.toFixed(2)}
        </div>
      </div>
    </div>
  )
}
