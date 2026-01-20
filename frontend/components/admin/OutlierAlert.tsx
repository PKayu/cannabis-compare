'use client'

import React from 'react'

interface OutlierAlertProps {
  outlier: {
    price_id: string
    product_name?: string
    dispensary_id: string
    amount: number
    state_average: number
    deviation_percent: number
    z_score: number
    severity: 'medium' | 'high'
    direction: 'above' | 'below'
  }
}

export function OutlierAlert({ outlier }: OutlierAlertProps) {
  const bgColor = outlier.severity === 'high' ? 'bg-red-50' : 'bg-orange-50'
  const borderColor = outlier.severity === 'high' ? 'border-red-200' : 'border-orange-200'
  const textColor = outlier.severity === 'high' ? 'text-red-700' : 'text-orange-700'
  const icon = outlier.severity === 'high' ? '🚨' : '⚠️'

  return (
    <div className={`${bgColor} ${borderColor} border rounded-lg p-4`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl">{icon}</span>
        <div className="flex-1">
          <p className={`font-semibold ${textColor}`}>
            Price Outlier Detected
          </p>
          {outlier.product_name && (
            <p className="text-gray-800 font-medium mt-1">{outlier.product_name}</p>
          )}
          <div className="mt-2 text-sm space-y-1">
            <p className="text-gray-600">
              <span className="font-medium">Current Price:</span> ${outlier.amount.toFixed(2)}
            </p>
            <p className="text-gray-600">
              <span className="font-medium">State Average:</span> ${outlier.state_average.toFixed(2)}
            </p>
            <p className={textColor}>
              <span className="font-medium">Deviation:</span>{' '}
              {Math.abs(outlier.deviation_percent).toFixed(1)}% {outlier.direction} average
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
            outlier.severity === 'high'
              ? 'bg-red-100 text-red-800'
              : 'bg-orange-100 text-orange-800'
          }`}>
            {outlier.severity.toUpperCase()}
          </span>
          <p className="text-xs text-gray-500 mt-1">
            z-score: {outlier.z_score.toFixed(2)}
          </p>
        </div>
      </div>
    </div>
  )
}

interface OutlierBadgeProps {
  severity: 'medium' | 'high'
  deviationPercent: number
}

export function OutlierBadge({ severity, deviationPercent }: OutlierBadgeProps) {
  const colors = severity === 'high'
    ? 'bg-red-100 text-red-800 border-red-200'
    : 'bg-orange-100 text-orange-800 border-orange-200'

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${colors}`}>
      {severity === 'high' ? '🚨' : '⚠️'}
      {Math.abs(deviationPercent).toFixed(0)}% {deviationPercent > 0 ? 'above' : 'below'}
    </span>
  )
}
