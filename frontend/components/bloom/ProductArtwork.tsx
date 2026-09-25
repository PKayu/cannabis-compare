import Image from 'next/image'

const imagery: Record<string, string> = {
  flower: 'flower', vaporizer: 'vape', edible: 'edible', tincture: 'tincture', topical: 'topical',
}
export default function ProductArtwork({ type, priority = false }: { type: string; priority?: boolean }) {
  const imageType = imagery[type.toLowerCase()]
  return <div className="relative flex aspect-[4/3] min-w-0 items-center justify-center overflow-hidden bg-bloom-parchment">
    {imageType ? <Image src={`/images/mountain-bloom/product-${imageType}.jpg`} alt={`Representative ${type} image; not the exact product`} fill unoptimized sizes="(max-width: 767px) 100vw, (max-width: 1279px) 45vw, 400px" className="object-cover" priority={priority} /> : <span className="px-5 text-center text-bloom-muted">Product image unavailable</span>}
    {imageType && <span className="absolute bottom-3 left-3 rounded-md bg-bloom-cream px-2 py-1 text-[11px] font-bold text-bloom-ink">Representative image</span>}
  </div>
}
