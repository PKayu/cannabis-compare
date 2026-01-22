import React from 'react'

interface PriceData {
  dispensary_id: string
  dispensary_name: string
  dispensary_location: string
  dispensary_hours: string | null
  dispensary_website: string | null
  msrp: number
  deal_price: number | null
  savings: number | null
  savings_percentage: number | null
  in_stock: boolean
  promotion: {
    id: string
    title: string
    description: string | null
    discount_percentage: number | null
    discount_amount: number | null
  } | null
  last_updated: string | null
}

interface PriceComparisonTableProps {
  prices: PriceData[]
  productId: string
}

// Deep link patterns for Utah dispensaries
const DISPENSARY_LINKS: Record<string, string> = {
  'wholesome-co': 'https://www.wholesomeco.com/search?q=',
  'dragonfly': 'https://dragonflywellness.com/search?q=',
  'curaleaf': 'https://curaleaf.com/search?q=',
  'beehive': 'https://beehivefarmacy.com/search?q=',
}

function generateOrderLink(dispensaryId: string, dispensaryWebsite: string | null, productName?: string): string {
  // Check if we have a known pattern
  const pattern = DISPENSARY_LINKS[dispensaryId.toLowerCase()]
  if (pattern && productName) {
    return pattern + encodeURIComponent(productName)
  }

  // Fall back to dispensary website
  if (dispensaryWebsite) {
    return dispensaryWebsite.startsWith('http') ? dispensaryWebsite : `https://${dispensaryWebsite}`
  }

  // Last resort: search
  return '#'
}

export default function PriceComparisonTable({ prices, productId }: PriceComparisonTableProps) {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-semibold text-gray-700">Dispensary</th>
              <th className="text-right px-4 py-3 text-sm font-semibold text-gray-700">MSRP</th>
              <th className="text-right px-4 py-3 text-sm font-semibold text-gray-700">Deal Price</th>
              <th className="text-center px-4 py-3 text-sm font-semibold text-gray-700">Stock</th>
              <th className="text-center px-4 py-3 text-sm font-semibold text-gray-700">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {prices.map((price, index) => (
              <tr
                key={price.dispensary_id}
                className={`hover:bg-gray-50 transition-colors ${index === 0 ? 'bg-green-50' : ''}`}
              >
                <td className="px-4 py-4">
                  <div>
                    <p className="font-semibold text-gray-900">
                      {price.dispensary_name}
                      {index === 0 && (
                        <span className="ml-2 px-2 py-0.5 bg-green-500 text-white text-xs rounded-full">
                          Best Price
                        </span>
                      )}
                    </p>
                    <p className="text-sm text-gray-600">{price.dispensary_location}</p>
                    {price.dispensary_hours && (
                      <p className="text-xs text-gray-500 mt-1">{price.dispensary_hours}</p>
                    )}
                  </div>
                </td>
                <td className="text-right px-4 py-4">
                  <span className={price.deal_price ? 'line-through text-gray-400' : 'font-semibold text-gray-900'}>
                    ${price.msrp.toFixed(2)}
                  </span>
                </td>
                <td className="text-right px-4 py-4">
                  {price.deal_price ? (
                    <div>
                      <p className="text-lg font-bold text-green-600">${price.deal_price.toFixed(2)}</p>
                      {price.promotion && (
                        <p className="text-xs text-green-600">
                          {price.savings_percentage}% off - {price.promotion.title}
                        </p>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td className="text-center px-4 py-4">
                  {price.in_stock ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5"></span>
                      In Stock
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-1.5"></span>
                      Out of Stock
                    </span>
                  )}
                </td>
                <td className="text-center px-4 py-4">
                  <a
                    href={generateOrderLink(price.dispensary_id, price.dispensary_website)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`inline-block px-4 py-2 rounded text-sm font-medium transition-colors ${
                      price.in_stock
                        ? 'bg-cannabis-600 text-white hover:bg-cannabis-700'
                        : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    }`}
                    onClick={(e) => !price.in_stock && e.preventDefault()}
                  >
                    {price.in_stock ? 'Order' : 'Unavailable'}
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden divide-y divide-gray-200">
        {prices.map((price, index) => (
          <div
            key={price.dispensary_id}
            className={`p-4 ${index === 0 ? 'bg-green-50' : ''}`}
          >
            <div className="flex justify-between items-start mb-3">
              <div>
                <p className="font-semibold text-gray-900">
                  {price.dispensary_name}
                  {index === 0 && (
                    <span className="ml-2 px-2 py-0.5 bg-green-500 text-white text-xs rounded-full">
                      Best
                    </span>
                  )}
                </p>
                <p className="text-sm text-gray-600">{price.dispensary_location}</p>
              </div>
              {price.in_stock ? (
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  In Stock
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                  Out of Stock
                </span>
              )}
            </div>

            <div className="flex justify-between items-center">
              <div>
                {price.deal_price ? (
                  <div>
                    <span className="line-through text-gray-400 text-sm mr-2">${price.msrp.toFixed(2)}</span>
                    <span className="text-lg font-bold text-green-600">${price.deal_price.toFixed(2)}</span>
                    {price.savings_percentage && (
                      <span className="ml-2 text-xs text-green-600">{price.savings_percentage}% off</span>
                    )}
                  </div>
                ) : (
                  <span className="text-lg font-semibold text-gray-900">${price.msrp.toFixed(2)}</span>
                )}
              </div>
              <a
                href={generateOrderLink(price.dispensary_id, price.dispensary_website)}
                target="_blank"
                rel="noopener noreferrer"
                className={`px-4 py-2 rounded text-sm font-medium ${
                  price.in_stock
                    ? 'bg-cannabis-600 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
                onClick={(e) => !price.in_stock && e.preventDefault()}
              >
                {price.in_stock ? 'Order' : 'Unavailable'}
              </a>
            </div>

            {price.promotion && (
              <p className="mt-2 text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                {price.promotion.title}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
