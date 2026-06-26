import React from 'react'

interface PriceData {
  dispensary_id: string
  dispensary_name: string
  dispensary_location: string
  dispensary_hours: string | null
  dispensary_website: string | null
  product_url: string | null
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
  productName?: string
}

const DISPENSARY_LINKS: Record<string, string> = {
  'wholesome-co': 'https://www.wholesomeco.com/search?q=',
  'dragonfly': 'https://dragonflywellness.com/search?q=',
  'curaleaf': 'https://curaleaf.com/search?q=',
  'beehive': 'https://beehivefarmacy.com/search?q=',
}

function generateOrderLink(
  dispensaryId: string,
  dispensaryWebsite: string | null,
  productUrl: string | null,
  productName?: string
): string {
  if (productUrl && productUrl.trim() !== '') {
    const url = productUrl.trim()
    return url.startsWith('http') ? url : `https://${url}`
  }
  if (dispensaryWebsite && dispensaryWebsite.trim() !== '') {
    const url = dispensaryWebsite.trim()
    return url.startsWith('http') ? url : `https://${url}`
  }
  const pattern = DISPENSARY_LINKS[dispensaryId.toLowerCase()]
  if (pattern && productName) return pattern + encodeURIComponent(productName)
  return '#'
}

export default function PriceComparisonTable({ prices, productId, productName }: PriceComparisonTableProps) {
  const effectivePrice = (p: PriceData) => p.deal_price ?? p.msrp
  const minPrice = Math.min(...prices.map(effectivePrice))
  const allSamePrice = prices.every(p => effectivePrice(p) === minPrice)
  const bestPriceIndex = allSamePrice ? -1 : prices.findIndex(p => effectivePrice(p) === minPrice)

  return (
    <div className="bg-groovy-cream border-2 border-groovy-ink rounded-2xl shadow-sticker overflow-hidden">

      {/* Desktop Table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead className="bg-groovy-teal border-b-2 border-groovy-ink">
            <tr>
              <th className="text-left px-5 py-3 text-xs font-display font-bold text-white uppercase tracking-wider">Dispensary</th>
              <th className="text-right px-5 py-3 text-xs font-display font-bold text-white uppercase tracking-wider">MSRP</th>
              <th className="text-right px-5 py-3 text-xs font-display font-bold text-white uppercase tracking-wider">Deal Price</th>
              <th className="text-center px-5 py-3 text-xs font-display font-bold text-white uppercase tracking-wider">Stock</th>
              <th className="text-center px-5 py-3 text-xs font-display font-bold text-white uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y-2 divide-stone-200">
            {prices.map((price, index) => (
              <tr
                key={price.dispensary_id}
                className={`transition-colors ${
                  index === bestPriceIndex ? 'bg-amber-50' : 'hover:bg-stone-50'
                }`}
              >
                <td className="px-5 py-4">
                  <div>
                    <p className="font-display font-bold text-groovy-ink flex items-center gap-2">
                      {price.dispensary_name}
                      {index === bestPriceIndex && (
                        <span className="px-2 py-0.5 bg-groovy-sun text-groovy-ink text-xs font-display font-bold rounded-full border-2 border-groovy-ink shadow-[2px_2px_0px_#1C1917]">
                          Best Price
                        </span>
                      )}
                    </p>
                    <p className="font-body text-sm text-stone-500">{price.dispensary_location}</p>
                    {price.dispensary_hours && (
                      <p className="font-body text-xs text-stone-400 mt-0.5">{price.dispensary_hours}</p>
                    )}
                  </div>
                </td>
                <td className="text-right px-5 py-4">
                  <span className={`font-body ${price.deal_price ? 'line-through text-stone-400 text-sm' : 'font-semibold text-groovy-ink'}`}>
                    ${price.msrp.toFixed(2)}
                  </span>
                </td>
                <td className="text-right px-5 py-4">
                  {price.deal_price ? (
                    <div>
                      <p className="font-display font-bold text-lg text-groovy-teal">${price.deal_price.toFixed(2)}</p>
                      {price.promotion && (
                        <p className="font-body text-xs text-groovy-teal mt-0.5">
                          {price.savings_percentage}% off — {price.promotion.title}
                        </p>
                      )}
                    </div>
                  ) : (
                    <span className="font-body text-stone-300">—</span>
                  )}
                </td>
                <td className="text-center px-5 py-4">
                  {price.in_stock ? (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-display font-bold bg-teal-50 text-groovy-teal border-2 border-groovy-teal">
                      <span className="w-1.5 h-1.5 bg-groovy-teal rounded-full"></span>
                      In Stock
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-display font-bold bg-stone-100 text-stone-500 border-2 border-stone-300">
                      <span className="w-1.5 h-1.5 bg-stone-400 rounded-full"></span>
                      Out of Stock
                    </span>
                  )}
                </td>
                <td className="text-center px-5 py-4">
                  <a
                    href={generateOrderLink(price.dispensary_id, price.dispensary_website, price.product_url, productName)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`inline-block px-4 py-2 rounded-xl text-sm font-display font-bold border-2 transition-all duration-150 ${
                      price.in_stock
                        ? 'bg-groovy-amber text-white border-groovy-ink shadow-[2px_2px_0px_#1C1917] hover:-translate-y-0.5 hover:shadow-[3px_3px_0px_#1C1917]'
                        : 'bg-stone-100 text-stone-400 border-stone-300 cursor-not-allowed'
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

      {/* Mobile Cards */}
      <div className="md:hidden divide-y-2 divide-stone-200">
        {prices.map((price, index) => (
          <div
            key={price.dispensary_id}
            className={`p-4 ${index === bestPriceIndex ? 'bg-amber-50' : ''}`}
          >
            <div className="flex justify-between items-start mb-3">
              <div>
                <p className="font-display font-bold text-groovy-ink">
                  {price.dispensary_name}
                  {index === bestPriceIndex && (
                    <span className="ml-2 px-2 py-0.5 bg-groovy-sun text-groovy-ink text-xs font-display font-bold rounded-full border border-groovy-ink">
                      Best
                    </span>
                  )}
                </p>
                <p className="font-body text-sm text-stone-500">{price.dispensary_location}</p>
              </div>
              {price.in_stock ? (
                <span className="px-2 py-0.5 rounded-full text-xs font-display font-bold bg-teal-50 text-groovy-teal border-2 border-groovy-teal">
                  In Stock
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full text-xs font-display font-bold bg-stone-100 text-stone-500 border-2 border-stone-300">
                  Out of Stock
                </span>
              )}
            </div>

            <div className="flex justify-between items-center">
              <div>
                {price.deal_price ? (
                  <div>
                    <span className="font-body line-through text-stone-400 text-sm mr-2">${price.msrp.toFixed(2)}</span>
                    <span className="font-display font-bold text-lg text-groovy-teal">${price.deal_price.toFixed(2)}</span>
                    {price.savings_percentage && (
                      <span className="ml-2 font-display text-xs font-bold text-groovy-teal">{price.savings_percentage}% off</span>
                    )}
                  </div>
                ) : (
                  <span className="font-display font-bold text-lg text-groovy-ink">${price.msrp.toFixed(2)}</span>
                )}
              </div>
              <a
                href={generateOrderLink(price.dispensary_id, price.dispensary_website, price.product_url, productName)}
                target="_blank"
                rel="noopener noreferrer"
                className={`px-4 py-2 rounded-xl text-sm font-display font-bold border-2 ${
                  price.in_stock
                    ? 'bg-groovy-amber text-white border-groovy-ink shadow-[2px_2px_0px_#1C1917]'
                    : 'bg-stone-100 text-stone-400 border-stone-300'
                }`}
                onClick={(e) => !price.in_stock && e.preventDefault()}
              >
                {price.in_stock ? 'Order' : 'Unavailable'}
              </a>
            </div>

            {price.promotion && (
              <p className="mt-2 font-body text-xs text-groovy-teal bg-teal-50 border border-groovy-teal px-3 py-1 rounded-xl">
                {price.promotion.title}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
