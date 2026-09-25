import Link from 'next/link'
import { money, offerDestination, updatedLabel, type ProductOffer } from '@/lib/product-contracts'

export default function PriceComparisonTable({ prices, weightGrams }: { prices: ProductOffer[]; weightGrams?: number | null }) {
  const available = prices.filter(price => price.in_stock)
  const lowest = available.length ? Math.min(...available.map(price => price.msrp)) : null
  return <div className="grid gap-5" aria-label="Dispensary offers">
    {prices.map((price, index) => {
      const destination = offerDestination(price)
      return <article key={`${price.dispensary_id}-${index}`} className="bloom-card grid gap-5 p-5 sm:p-6 md:grid-cols-[minmax(0,1fr)_minmax(0,0.7fr)_minmax(0,0.9fr)] md:items-start">
        <div className="min-w-0"><Link href={`/dispensaries/${price.dispensary_id}`} className="inline-flex min-h-[44px] items-center text-lg font-bold underline decoration-bloom-ink/30 underline-offset-4 hover:decoration-bloom-ink">{price.dispensary_name}</Link><p className="text-sm text-bloom-navy/75">{price.dispensary_location || 'Location not reported'}</p>{price.dispensary_hours && <p className="mt-2 text-sm text-bloom-navy/75">{price.dispensary_hours}</p>}<p className="mt-3 text-xs text-bloom-navy/70">{updatedLabel(price.last_updated)}</p></div>
        <div className="tabular-nums"><p className="text-xs font-bold uppercase tracking-wider text-bloom-navy/75">Listed price</p><p className="mt-1 text-3xl font-bold">{money(price.msrp)}</p>{weightGrams != null && weightGrams > 0 && <p className="text-sm text-bloom-navy/75">{money(price.msrp / weightGrams)} / g</p>}{price.in_stock && price.msrp === lowest && <p className="mt-2 inline-flex rounded-full border border-bloom-ink/20 bg-bloom-mustard px-3 py-1 text-xs font-bold">Lowest listed in-stock price</p>}{price.deal_price != null && <div className="mt-3 border-l-2 border-bloom-orange pl-3 text-sm"><p className="font-bold">Possible promotion: {money(price.deal_price)}</p>{price.promotion && <p>{price.promotion.title}</p>}<p className="mt-1 text-bloom-navy/75">Estimated from dispensary promotions. Confirm eligibility and final price.</p></div>}</div>
        <div className="flex flex-col items-start gap-3"><p className={`rounded-full border px-3 py-1 text-sm font-bold ${price.in_stock ? 'border-bloom-ink/20 bg-bloom-blue text-bloom-cream' : 'border-bloom-ink/20 bg-bloom-parchment text-bloom-navy/75'}`}>{price.in_stock ? 'Listed in stock' : 'Out of stock'}</p>{price.in_stock && destination ? <a className="bloom-button w-full text-center" href={destination.href} target="_blank" rel="noopener noreferrer">{destination.label} ↗<span className="sr-only"> — {price.dispensary_name}, opens in a new tab</span></a> : <p className="text-sm text-bloom-navy/75">{price.in_stock ? 'No dispensary link available.' : 'This offering is currently unavailable.'}</p>}{price.in_stock && destination && <p className="text-xs text-bloom-navy/75">Opens the dispensary site in a new tab. Purchases happen there, not here.</p>}</div>
      </article>
    })}
  </div>
}
