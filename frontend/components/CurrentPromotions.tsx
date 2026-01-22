import React from 'react'

interface Promotion {
  id: string
  title: string
  description: string | null
  discount_percentage: number | null
  discount_amount: number | null
  recurring_pattern: string | null
  start_date: string
  end_date: string | null
}

interface CurrentPromotionsProps {
  promotions: Promotion[]
}

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function getRecurringDayLabel(pattern: string | null): string | null {
  if (!pattern) return null

  // Handle patterns like "weekly" or "monday", "tuesday", etc.
  const lowerPattern = pattern.toLowerCase()

  if (lowerPattern === 'weekly') return 'Every Week'
  if (lowerPattern === 'daily') return 'Every Day'
  if (lowerPattern === 'monthly') return 'Monthly'

  // Check if it's a day of the week
  const day = DAYS_OF_WEEK.find(d => lowerPattern.includes(d.toLowerCase()))
  if (day) return `Every ${day}`

  return pattern
}

function formatEndDate(endDate: string | null): string | null {
  if (!endDate) return null
  const date = new Date(endDate)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function CurrentPromotions({ promotions }: CurrentPromotionsProps) {
  if (promotions.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-600">
        No active promotions at this time.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {promotions.map((promo) => {
        const recurringLabel = getRecurringDayLabel(promo.recurring_pattern)
        const endDateLabel = formatEndDate(promo.end_date)

        return (
          <div
            key={promo.id}
            className="bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-500 rounded-r-lg p-4 shadow-sm"
          >
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-2">
              <div className="flex-1">
                <h3 className="font-bold text-green-900 text-lg">{promo.title}</h3>
                {promo.description && (
                  <p className="text-green-700 mt-1">{promo.description}</p>
                )}

                <div className="flex flex-wrap items-center gap-3 mt-3">
                  {/* Discount Badge */}
                  {promo.discount_percentage && (
                    <span className="inline-flex items-center px-3 py-1 bg-green-500 text-white text-sm font-bold rounded-full">
                      {promo.discount_percentage}% OFF
                    </span>
                  )}
                  {promo.discount_amount && !promo.discount_percentage && (
                    <span className="inline-flex items-center px-3 py-1 bg-green-500 text-white text-sm font-bold rounded-full">
                      ${promo.discount_amount} OFF
                    </span>
                  )}

                  {/* Recurring Pattern */}
                  {recurringLabel && (
                    <span className="inline-flex items-center text-sm text-green-700">
                      <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      {recurringLabel}
                    </span>
                  )}

                  {/* End Date */}
                  {endDateLabel && (
                    <span className="inline-flex items-center text-sm text-gray-600">
                      <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      Ends {endDateLabel}
                    </span>
                  )}
                </div>
              </div>

              {/* Deal Icon */}
              <div className="hidden md:flex items-center justify-center w-16 h-16 bg-green-100 rounded-full">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>
        )
      })}

      {/* Weekly Deals Calendar Preview */}
      {promotions.some(p => p.recurring_pattern) && (
        <div className="mt-6 bg-white rounded-lg border p-4">
          <h4 className="font-semibold text-gray-800 mb-3">Weekly Deals Schedule</h4>
          <div className="grid grid-cols-7 gap-1">
            {DAYS_OF_WEEK.map((day) => {
              const dayPromos = promotions.filter(p => {
                if (!p.recurring_pattern) return false
                return p.recurring_pattern.toLowerCase().includes(day.toLowerCase())
              })

              return (
                <div
                  key={day}
                  className={`p-2 rounded text-center ${
                    dayPromos.length > 0
                      ? 'bg-green-50 border border-green-200'
                      : 'bg-gray-50'
                  }`}
                >
                  <p className="text-xs font-medium text-gray-600">{day.slice(0, 3)}</p>
                  {dayPromos.length > 0 && (
                    <div className="mt-1">
                      <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
