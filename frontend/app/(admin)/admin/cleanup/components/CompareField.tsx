'use client'

import React from 'react'

/**
 * Read-only comparison row: highlights green when both sides agree,
 * yellow when they differ. Used by FlagCard (scraped vs matched/current)
 * and DuplicatePairCard (product A vs product B).
 */
export function CompareField({ label, scraped, matched }: { label: string; scraped: string; matched: string }) {
  const match = scraped.toLowerCase().trim() === matched.toLowerCase().trim()
  const bg = !scraped && !matched ? '' : match ? 'bg-green-50' : 'bg-yellow-50'
  return (
    <div className={`flex justify-between px-2 py-0.5 rounded ${bg}`}>
      <span className="text-gray-500 text-xs w-12">{label}:</span>
      <span className="text-xs font-medium text-gray-900 truncate">{matched || 'N/A'}</span>
    </div>
  )
}
