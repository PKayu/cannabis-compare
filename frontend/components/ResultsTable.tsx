import React from 'react'
import Link from 'next/link'
import DealBadge from './DealBadge'

interface Product {
  id: string
  name: string
  brand: string | null
  type: string
  thc: number | null
  cbd: number | null
  min_price: number
  max_price: number
  dispensary_count: number
  relevance_score: number
}

interface ResultsTableProps {
  products: Product[]
}

export default function ResultsTable({ products }: ResultsTableProps) {
  // Mobile card layout
  const MobileCard = ({ product }: { product: Product }) => (
    <Link href={`/products/${product.id}`}>
      <div className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow cursor-pointer border border-gray-200">
        <div className="flex justify-between items-start mb-2">
          <div className="flex-1">
            <h3 className="font-semibold text-lg text-gray-900">{product.name}</h3>
            {product.brand && (
              <p className="text-sm text-gray-600">{product.brand}</p>
            )}
          </div>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded uppercase">
            {product.type}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
          {product.thc !== null && (
            <div>
              <span className="text-gray-500">THC:</span>
              <span className="ml-1 font-medium text-gray-900">{product.thc}%</span>
            </div>
          )}
          {product.cbd !== null && (
            <div>
              <span className="text-gray-500">CBD:</span>
              <span className="ml-1 font-medium text-gray-900">{product.cbd}%</span>
            </div>
          )}
        </div>

        <div className="flex justify-between items-center pt-3 border-t border-gray-100">
          <div>
            <div className="text-lg font-bold text-cannabis-700">
              ${product.min_price.toFixed(2)}
              {product.min_price !== product.max_price && (
                <span className="text-sm text-gray-500"> - ${product.max_price.toFixed(2)}</span>
              )}
            </div>
            <div className="text-xs text-gray-500">
              {product.dispensary_count} {product.dispensary_count === 1 ? 'dispensary' : 'dispensaries'}
            </div>
          </div>
          <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </Link>
  )

  // Desktop table layout
  return (
    <>
      {/* Mobile View */}
      <div className="lg:hidden space-y-3">
        {products.map((product) => (
          <MobileCard key={product.id} product={product} />
        ))}
      </div>

      {/* Desktop View */}
      <div className="hidden lg:block bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Product
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                THC %
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                CBD %
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Price Range
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Locations
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">

              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {products.map((product) => (
              <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4">
                  <Link href={`/products/${product.id}`} className="block">
                    <div className="font-medium text-gray-900 hover:text-cannabis-600">
                      {product.name}
                    </div>
                    {product.brand && (
                      <div className="text-sm text-gray-500">{product.brand}</div>
                    )}
                  </Link>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-600">{product.type}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-900">
                    {product.thc !== null ? `${product.thc}%` : '-'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-900">
                    {product.cbd !== null ? `${product.cbd}%` : '-'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-semibold text-cannabis-700">
                    ${product.min_price.toFixed(2)}
                    {product.min_price !== product.max_price && (
                      <span className="text-gray-500"> - ${product.max_price.toFixed(2)}</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-600">
                    {product.dispensary_count} {product.dispensary_count === 1 ? 'location' : 'locations'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <Link
                    href={`/products/${product.id}`}
                    className="text-cannabis-600 hover:text-cannabis-700 font-medium text-sm"
                  >
                    View Details →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
