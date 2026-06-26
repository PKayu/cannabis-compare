import React from 'react'
import Link from 'next/link'
import DealBadge from './DealBadge'
import CannabisLeaf from './CannabisLeaf'

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
  available_weights?: string[]
  relevance_score: number
}

interface ResultsTableProps {
  products: Product[]
}

const TYPE_COLORS: Record<string, string> = {
  flower: 'bg-green-100 text-green-800',
  concentrate: 'bg-orange-100 text-orange-800',
  edible: 'bg-yellow-100 text-yellow-800',
  vaporizer: 'bg-blue-100 text-blue-800',
  topical: 'bg-purple-100 text-purple-800',
  tincture: 'bg-teal-100 text-teal-800',
  'pre-roll': 'bg-amber-100 text-amber-800',
  hardware: 'bg-stone-100 text-stone-700',
}

export default function ResultsTable({ products }: ResultsTableProps) {
  const MobileCard = ({ product }: { product: Product }) => (
    <Link href={`/products/${product.id}`}>
      <div className="bg-groovy-cream border-2 border-groovy-ink rounded-2xl shadow-sticker p-4 hover:-translate-y-0.5 hover:shadow-sticker-lg transition-all duration-150 cursor-pointer">
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1 pr-2">
            <h3 className="font-display font-bold text-base text-groovy-ink leading-tight">{product.name}</h3>
            {product.brand && (
              <p className="font-body text-sm text-stone-500 mt-0.5">{product.brand}</p>
            )}
          </div>
          <span className={`text-xs font-display font-bold px-2 py-1 rounded-full border-2 border-groovy-ink flex-shrink-0 ${TYPE_COLORS[product.type] ?? 'bg-stone-100 text-stone-700'}`}>
            {product.type}
          </span>
        </div>

        <div className="flex gap-4 mb-3 text-sm font-body">
          {product.thc !== null && (
            <div>
              <span className="text-stone-500">THC </span>
              <span className="font-semibold text-groovy-ink">{product.thc}%</span>
            </div>
          )}
          {product.cbd !== null && (
            <div>
              <span className="text-stone-500">CBD </span>
              <span className="font-semibold text-groovy-ink">{product.cbd}%</span>
            </div>
          )}
        </div>

        {product.available_weights && product.available_weights.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {product.available_weights.map((w) => (
              <span key={w} className="px-2 py-0.5 bg-amber-50 text-groovy-ink text-xs font-display font-semibold rounded-full border-2 border-groovy-ink">
                {w}
              </span>
            ))}
          </div>
        )}

        <div className="flex justify-between items-center pt-3 border-t-2 border-stone-200">
          <div>
            <div className="font-display font-bold text-lg text-groovy-teal">
              ${product.min_price.toFixed(2)}
              {product.min_price !== product.max_price && (
                <span className="text-sm text-stone-400 font-body font-normal"> – ${product.max_price.toFixed(2)}</span>
              )}
            </div>
            <div className="font-body text-xs text-stone-500">
              {product.dispensary_count} {product.dispensary_count === 1 ? 'dispensary' : 'dispensaries'}
            </div>
          </div>
          <div className="text-groovy-amber font-display font-bold text-sm">View →</div>
        </div>
      </div>
    </Link>
  )

  return (
    <>
      {/* Mobile */}
      <div className="lg:hidden space-y-3">
        {products.map((product) => (
          <MobileCard key={product.id} product={product} />
        ))}
      </div>

      {/* Desktop */}
      <div className="hidden lg:block bg-groovy-cream border-2 border-groovy-ink rounded-2xl shadow-sticker overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-groovy-teal border-b-2 border-groovy-ink">
            <tr>
              {['Product', 'Type', 'THC %', 'CBD %', 'Price Range', 'Locations', ''].map((h) => (
                <th key={h} className="px-5 py-3 text-left text-xs font-display font-bold text-white uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y-2 divide-stone-200">
            {products.map((product) => (
              <tr key={product.id} className="hover:bg-amber-50 transition-colors group">
                <td className="px-5 py-4">
                  <Link href={`/products/${product.id}`} className="block">
                    <div className="font-display font-bold text-groovy-ink group-hover:text-groovy-teal transition-colors">
                      {product.name}
                    </div>
                    {product.brand && (
                      <div className="font-body text-sm text-stone-500">{product.brand}</div>
                    )}
                    {product.available_weights && product.available_weights.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {product.available_weights.map((w) => (
                          <span key={w} className="px-2 py-0.5 bg-amber-50 text-groovy-ink text-xs font-display font-semibold rounded-full border-2 border-groovy-ink">
                            {w}
                          </span>
                        ))}
                      </div>
                    )}
                  </Link>
                </td>
                <td className="px-5 py-4 whitespace-nowrap">
                  <span className={`text-xs font-display font-bold px-2 py-1 rounded-full border-2 border-groovy-ink ${TYPE_COLORS[product.type] ?? 'bg-stone-100 text-stone-700'}`}>
                    {product.type}
                  </span>
                </td>
                <td className="px-5 py-4 whitespace-nowrap font-body text-sm text-groovy-ink">
                  {product.thc !== null ? `${product.thc}%` : '—'}
                </td>
                <td className="px-5 py-4 whitespace-nowrap font-body text-sm text-groovy-ink">
                  {product.cbd !== null ? `${product.cbd}%` : '—'}
                </td>
                <td className="px-5 py-4 whitespace-nowrap">
                  <div className="font-display font-bold text-groovy-teal">
                    ${product.min_price.toFixed(2)}
                    {product.min_price !== product.max_price && (
                      <span className="text-stone-400 font-body font-normal text-sm"> – ${product.max_price.toFixed(2)}</span>
                    )}
                  </div>
                </td>
                <td className="px-5 py-4 whitespace-nowrap font-body text-sm text-stone-600">
                  {product.dispensary_count} {product.dispensary_count === 1 ? 'location' : 'locations'}
                </td>
                <td className="px-5 py-4 whitespace-nowrap text-right">
                  <Link
                    href={`/products/${product.id}`}
                    className="font-display font-bold text-sm text-groovy-amber hover:text-groovy-rust transition-colors"
                  >
                    Details →
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
