import Link from 'next/link'
import ProductArtwork from '@/components/bloom/ProductArtwork'
import { money, potency, type SearchProduct } from '@/lib/product-contracts'

export default function ResultsTable({ products, returnTo = '/products/search' }: { products: SearchProduct[]; returnTo?: string }) {
  return <ul className="grid min-w-0 gap-6 md:grid-cols-2" aria-label="Product results">
    {products.map(product => <li key={product.id} className="bloom-panel min-w-0 overflow-hidden" data-testid="product-card">
      <ProductArtwork type={product.type} />
      <div className="p-5 sm:p-6">
        <p className="text-xs font-bold uppercase tracking-wider text-bloom-muted">{product.type}</p>
        <h3 className="mt-1 text-2xl font-bold leading-tight"><Link className="inline-flex min-h-[44px] items-center hover:underline" href={`/products/${product.id}?returnTo=${encodeURIComponent(returnTo)}`}>{product.name}</Link></h3>
        <p className="mt-1 text-sm text-bloom-muted">{product.brand ?? 'Brand not reported'}</p>
        <dl className="mt-5 grid grid-cols-2 gap-3 border-y border-bloom-line py-3 text-sm"><div><dt className="text-bloom-muted">THC</dt><dd className="font-bold tabular-nums">{potency(product.thc)}</dd></div><div><dt className="text-bloom-muted">CBD</dt><dd className="font-bold tabular-nums">{potency(product.cbd)}</dd></div></dl>
        <p className="mt-4 text-xs font-bold text-bloom-muted">Available weights</p><p className="mt-1 text-sm">{product.available_weights?.length ? product.available_weights.join(' · ') : 'Package size not reported'}</p>
        <div className="mt-5"><p className="text-2xl font-bold tabular-nums">{money(product.min_price)}{product.min_price !== product.max_price && <span className="text-lg"> – {money(product.max_price)}</span>}</p><p className="mt-1 text-sm text-bloom-muted">Across {product.dispensary_count} {product.dispensary_count === 1 ? 'dispensary' : 'dispensaries'} · all listed sizes</p></div>
        <Link href={`/products/${product.id}?returnTo=${encodeURIComponent(returnTo)}`} className="bloom-button-secondary mt-5 w-full" aria-label={`Compare sizes and prices for ${product.name}`}>Compare sizes & prices <span aria-hidden="true">→</span></Link>
      </div>
    </li>)}
  </ul>
}
