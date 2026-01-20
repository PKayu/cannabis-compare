'use client'

import React, { useState } from 'react'

interface Product {
  id: string
  name: string
  brand?: string | null
  thc_percentage?: number | null
  cbd_percentage?: number | null
  product_type?: string
  price_count?: number
}

interface MergePreviewProps {
  sourceProduct: Product
  targetProduct: Product
  onMerge: () => Promise<void>
  onCancel: () => void
}

export function MergePreview({
  sourceProduct,
  targetProduct,
  onMerge,
  onCancel
}: MergePreviewProps) {
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleMerge = async () => {
    setProcessing(true)
    setError(null)
    try {
      await onMerge()
    } catch (err) {
      setError('Failed to merge products. Please try again.')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 overflow-hidden">
        <div className="bg-blue-600 px-6 py-4">
          <h3 className="text-lg font-bold text-white">Merge Products</h3>
        </div>

        <div className="p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-6">
            {/* Source Product */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm font-medium text-red-700 mb-2">
                Will be merged (source)
              </p>
              <p className="font-bold text-gray-900">{sourceProduct.name}</p>
              {sourceProduct.brand && (
                <p className="text-sm text-gray-600">Brand: {sourceProduct.brand}</p>
              )}
              {sourceProduct.thc_percentage && (
                <p className="text-sm text-gray-600">THC: {sourceProduct.thc_percentage}%</p>
              )}
              {sourceProduct.price_count !== undefined && (
                <p className="text-sm text-gray-600 mt-2">
                  {sourceProduct.price_count} price{sourceProduct.price_count !== 1 ? 's' : ''} will be moved
                </p>
              )}
            </div>

            {/* Arrow */}
            <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2">
              <span className="text-2xl">→</span>
            </div>

            {/* Target Product */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm font-medium text-green-700 mb-2">
                Will remain (target)
              </p>
              <p className="font-bold text-gray-900">{targetProduct.name}</p>
              {targetProduct.brand && (
                <p className="text-sm text-gray-600">Brand: {targetProduct.brand}</p>
              )}
              {targetProduct.thc_percentage && (
                <p className="text-sm text-gray-600">THC: {targetProduct.thc_percentage}%</p>
              )}
            </div>
          </div>

          <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              <strong>Warning:</strong> This action cannot be undone. All prices from{' '}
              <strong>{sourceProduct.name}</strong> will be reassigned to{' '}
              <strong>{targetProduct.name}</strong>.
            </p>
          </div>
        </div>

        <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            disabled={processing}
          >
            Cancel
          </button>
          <button
            onClick={handleMerge}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            disabled={processing}
          >
            {processing ? 'Merging...' : 'Confirm Merge'}
          </button>
        </div>
      </div>
    </div>
  )
}
