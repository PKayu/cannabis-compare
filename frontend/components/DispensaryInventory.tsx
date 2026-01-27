'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'

interface InventoryItem {
  product_id: string
  product_name: string
  brand: string | null
  product_type: string
  thc_percentage: number | null
  cbd_percentage: number | null
  price: number
  in_stock: boolean
  last_updated: string | null
}

interface DispensaryInventoryProps {
  dispensaryId: string
}

// Product types with value (matches DB) and label (display text)
// DB stores lowercase: 'flower', 'vaporizer', 'edible', etc.
const PRODUCT_TYPES = [
  { value: 'All', label: 'All' },
  { value: 'flower', label: 'Flower' },
  { value: 'vaporizer', label: 'Vape' },
  { value: 'edible', label: 'Edible' },
  { value: 'concentrate', label: 'Concentrate' },
  { value: 'tincture', label: 'Tincture' },
  { value: 'topical', label: 'Topical' },
]
const SORT_OPTIONS = [
  { value: 'name', label: 'Name' },
  { value: 'price_low', label: 'Price: Low to High' },
  { value: 'price_high', label: 'Price: High to Low' },
  { value: 'thc', label: 'THC %' },
  { value: 'cbd', label: 'CBD %' },
]

export default function DispensaryInventory({ dispensaryId }: DispensaryInventoryProps) {
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [productType, setProductType] = useState('All')
  const [sortBy, setSortBy] = useState('name')

  useEffect(() => {
    loadInventory()
  }, [dispensaryId, productType, sortBy])

  const loadInventory = async () => {
    try {
      setLoading(true)
      setError(null)

      const params: any = { sort_by: sortBy }
      if (productType !== 'All') {
        params.product_type = productType
      }

      const res = await api.dispensaries.getInventory(dispensaryId, params)
      setInventory(res.data)
    } catch (err) {
      console.error('Failed to load inventory:', err)
      setError('Failed to load inventory')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Filters */}
      <div className="p-4 border-b flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          {PRODUCT_TYPES.map((type) => (
            <button
              key={type.value}
              onClick={() => setProductType(type.value)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                productType === type.value
                  ? 'bg-cannabis-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {type.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded text-sm"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cannabis-600"></div>
          <p className="mt-2 text-gray-600">Loading inventory...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-8 text-center text-red-600">
          {error}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && inventory.length === 0 && (
        <div className="p-8 text-center text-gray-600">
          No products found{productType !== 'All' ? ` for ${productType}` : ''}.
        </div>
      )}

      {/* Desktop Table */}
      {!loading && !error && inventory.length > 0 && (
        <>
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-3 text-sm font-semibold text-gray-700">Product</th>
                  <th className="text-left px-4 py-3 text-sm font-semibold text-gray-700">Type</th>
                  <th className="text-right px-4 py-3 text-sm font-semibold text-gray-700">THC</th>
                  <th className="text-right px-4 py-3 text-sm font-semibold text-gray-700">CBD</th>
                  <th className="text-right px-4 py-3 text-sm font-semibold text-gray-700">Price</th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-700">Stock</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {inventory.map((item) => (
                  <tr key={item.product_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link
                        href={`/products/${item.product_id}`}
                        className="font-medium text-gray-900 hover:text-cannabis-600"
                      >
                        {item.product_name}
                      </Link>
                      {item.brand && (
                        <p className="text-sm text-gray-500">{item.brand}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                        {item.product_type}
                      </span>
                    </td>
                    <td className="text-right px-4 py-3 text-gray-700">
                      {item.thc_percentage !== null ? `${item.thc_percentage}%` : '—'}
                    </td>
                    <td className="text-right px-4 py-3 text-gray-700">
                      {item.cbd_percentage !== null ? `${item.cbd_percentage}%` : '—'}
                    </td>
                    <td className="text-right px-4 py-3 font-semibold text-gray-900">
                      ${item.price.toFixed(2)}
                    </td>
                    <td className="text-center px-4 py-3">
                      {item.in_stock ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          In Stock
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                          Out
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Card View */}
          <div className="md:hidden divide-y divide-gray-200">
            {inventory.map((item) => (
              <div key={item.product_id} className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <Link
                      href={`/products/${item.product_id}`}
                      className="font-medium text-gray-900 hover:text-cannabis-600"
                    >
                      {item.product_name}
                    </Link>
                    {item.brand && (
                      <p className="text-sm text-gray-500">{item.brand}</p>
                    )}
                  </div>
                  <span className="text-lg font-bold text-gray-900">${item.price.toFixed(2)}</span>
                </div>

                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                      {item.product_type}
                    </span>
                    {item.thc_percentage !== null && (
                      <span className="text-sm text-gray-600">THC: {item.thc_percentage}%</span>
                    )}
                  </div>
                  {item.in_stock ? (
                    <span className="text-xs text-green-600">In Stock</span>
                  ) : (
                    <span className="text-xs text-gray-500">Out of Stock</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Footer with count */}
      {!loading && !error && inventory.length > 0 && (
        <div className="p-4 border-t bg-gray-50 text-sm text-gray-600">
          Showing {inventory.length} product{inventory.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}
