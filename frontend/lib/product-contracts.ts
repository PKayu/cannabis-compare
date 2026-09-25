/** Public API shapes. Keep nulls explicit; prices belong to variants. */
export interface SearchProduct {
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

export interface Variant { id: string; weight: string | null; weight_grams: number | null }
export interface ProductDetail {
  id: string
  name: string
  brand: string | null
  brand_id: string | null
  product_type: string
  thc_percentage: number | null
  cbd_percentage: number | null
  is_master: boolean
  normalization_confidence: number | null
  variants: Variant[]
  created_at: string | null
  updated_at: string | null
}
export interface ProductOffer {
  dispensary_id: string
  dispensary_name: string
  dispensary_location: string | null
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
export interface WeightGroup { variant_id: string; weight: string | null; weight_grams: number | null; prices: ProductOffer[] }
export interface RelatedProduct {
  id: string
  name: string
  brand: string | null
  product_type: string
  thc_percentage: number | null
  cbd_percentage: number | null
  min_price: number | null
  max_price: number | null
  similarity_score?: number
}
export interface PriceHistoryPoint { date: string; min: number; max: number; avg: number }

export const money = (value: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
export const potency = (value: number | null | undefined) => value == null ? 'Not reported' : `${value}%`
export const offerPrice = (offer: ProductOffer) => offer.deal_price ?? offer.msrp

/** Preserve package boundaries, including unknown sizes and variants without prices. */
export function comparisonGroups(product: ProductDetail, groups: WeightGroup[]): WeightGroup[] {
  const known = new Set(groups.map(group => group.variant_id))
  return [...groups, ...product.variants.filter(variant => !known.has(variant.id)).map(variant => ({
    variant_id: variant.id, weight: variant.weight, weight_grams: variant.weight_grams, prices: [],
  }))]
}

/** Accept explicit web URLs or bare domains from scrapers, never credentials or other schemes. */
export function safeDispensaryUrl(raw: string | null): string | null {
  if (!raw?.trim()) return null
  const value = raw.trim()
  if (/^[a-z][a-z\d+.-]*:/i.test(value) && !/^https?:\/\//i.test(value)) return null
  if (value.startsWith('/') || /[\s\\]/.test(value)) return null
  try {
    const url = new URL(/^https?:\/\//i.test(value) ? value : `https://${value}`)
    if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password || !url.hostname.includes('.')) return null
    return url.href
  } catch { return null }
}

export function offerDestination(offer: ProductOffer) {
  const product = safeDispensaryUrl(offer.product_url)
  if (product) return { href: product, label: 'View at dispensary' }
  const website = safeDispensaryUrl(offer.dispensary_website)
  return website ? { href: website, label: 'Visit dispensary website' } : null
}

export function updatedLabel(value: string | null): string {
  if (!value) return 'Update time not reported'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Update time not reported'
  return `Updated ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })}`
}
