import React from 'react'
import Link from 'next/link'

interface Dispensary {
  id: string
  name: string
  location: string
  hours: string | null
  website: string | null
  product_count: number
  active_promotions: number
  created_at: string | null
}

interface DispensaryListProps {
  dispensaries: Dispensary[]
}

export default function DispensaryList({ dispensaries }: DispensaryListProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {dispensaries.map((dispensary) => (
        <Link
          key={dispensary.id}
          href={`/dispensaries/${dispensary.id}`}
          className="block bg-white rounded-lg shadow hover:shadow-md transition-shadow"
        >
          <div className="p-6">
            {/* Header */}
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 hover:text-cannabis-600">
                  {dispensary.name}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {dispensary.location}
                </p>
              </div>
              {dispensary.active_promotions > 0 && (
                <span className="inline-flex items-center px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                  {dispensary.active_promotions} Deal{dispensary.active_promotions !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            {/* Hours */}
            {dispensary.hours && (
              <div className="mt-4 flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {dispensary.hours}
              </div>
            )}

            {/* Stats */}
            <div className="mt-4 flex items-center justify-between border-t pt-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-cannabis-600">{dispensary.product_count}</p>
                <p className="text-xs text-gray-500">Products</p>
              </div>

              {dispensary.website && (
                <a
                  href={dispensary.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="px-3 py-1 text-sm text-cannabis-600 border border-cannabis-600 rounded hover:bg-cannabis-50 transition-colors"
                >
                  Visit Website
                </a>
              )}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
