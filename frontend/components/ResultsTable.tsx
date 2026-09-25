import Link from 'next/link'
import ProductArtwork from '@/components/bloom/ProductArtwork'
import { money, potency, type SearchProduct } from '@/lib/product-contracts'

export default function ResultsTable({ products, returnTo = '/products/search' }: { products: SearchProduct[]; returnTo?: string }) {
  return <ul className="grid min-w-0 gap-6 md:grid-cols-2" aria-label="Product results">
    {products.map(product => <li key={product.id} className="bloom-card min-w-0 overflow-hidden transition-transform duration-200 hover:-translate-y-1 hover:shadow-[6px_6px_0_#102A32]" data-testid="product-card">
      <ProductArtwork type={product.type} />
      <div className="p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-[0.16em] text-bloom-navy/75">{product.type}</p><h3 className="mt-1 text-2xl font-bold leading-tight"><Link className="inline-flex min-h-[44px] items-center underline-offset-4 hover:underline" href={`/products/${product.id}?returnTo=${encodeURIComponent(returnTo)}`}>{product.name}</Link></h3><p className="mt-1 text-sm text-bloom-navy/75">{product.brand ?? 'Brand not reported'}</p></div><span className="rounded-full border border-bloom-ink/20 bg-bloom-mustard px-3 py-1 text-xs font-bold text-bloom-ink">{product.dispensary_count} {product.dispensary_count === 1 ? 'shop' : 'shops'}</span></div>
        <dl className="mt-5 grid grid-cols-2 gap-3 border-y border-bloom-ink/20 py-3 text-sm"><div><dt className="text-bloom-navy/75">THC</dt><dd className="font-bold tabular-nums">{potency(product.thc)}</dd></div><div><dt className="text-bloom-navy/75">CBD</dt><dd className="font-bold tabular-nums">{potency(product.cbd)}</dd></div></dl>
        <p className="mt-4 text-xs font-bold uppercase tracking-[0.13em] text-bloom-navy/75">Available weights</p><p className="mt-1 text-sm font-medium">{product.available_weights?.length ? product.available_weights.join(' · ') : 'Package size not reported'}</p>
        <div className="mt-5 flex flex-wrap items-end justify-between gap-3"><div><p className="text-2xl font-bold tabular-nums">{money(product.min_price)}{product.min_price !== product.max_price && <span className="text-lg"> – {money(product.max_price)}</span>}</p><p className="mt-1 text-sm text-bloom-navy/75">Listed across all available sizes</p></div><Link href={`/products/${product.id}?returnTo=${encodeURIComponent(returnTo)}`} className="bloom-button mt-1" aria-label={`Compare sizes and prices for ${product.name}`}>Compare <span aria-hidden="true">→</span></Link></div>
      </div>
    </li>)}
  </ul>
}
