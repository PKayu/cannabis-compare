export type SortOrder = 'relevance' | 'price_low' | 'price_high' | 'thc' | 'cbd'
export interface SearchFilters {
  productType: string
  minPrice?: number
  maxPrice?: number
  minThc?: number
  maxThc?: number
  minCbd?: number
  maxCbd?: number
  sortBy: SortOrder
}
export const DEFAULT_FILTERS: SearchFilters = { productType: '', sortBy: 'relevance' }
export const PRODUCT_TYPES = ['', 'flower', 'concentrate', 'edible', 'vaporizer', 'topical', 'tincture', 'pre-roll', 'hardware']
export const SORT_OPTIONS: { value: SortOrder; label: string }[] = [
  { value: 'relevance', label: 'Best match' }, { value: 'price_low', label: 'Price: low to high' },
  { value: 'price_high', label: 'Price: high to low' }, { value: 'thc', label: 'THC: high to low' },
  { value: 'cbd', label: 'CBD: high to low' },
]
const ranges = [
  ['minPrice', 'min_price', undefined], ['maxPrice', 'max_price', undefined],
  ['minThc', 'min_thc', 100], ['maxThc', 'max_thc', 100],
  ['minCbd', 'min_cbd', 100], ['maxCbd', 'max_cbd', 100],
] as const

export function readSearch(params: URLSearchParams) {
  const filters: SearchFilters = { ...DEFAULT_FILTERS }
  const type = params.get('product_type') ?? ''
  // Preserve server-supported categories in existing deep links, even if not in the quick select.
  filters.productType = type
  const sort = params.get('sort_by')
  if (SORT_OPTIONS.some(option => option.value === sort)) filters.sortBy = sort as SortOrder
  for (const [field, key, max] of ranges) {
    const raw = params.get(key)
    if (raw === null || raw.trim() === '') continue
    const value = Number(raw)
    if (Number.isFinite(value) && value >= 0 && (max === undefined || value <= max)) filters[field] = value
  }
  return { query: (params.get('q') ?? '').trim(), filters }
}
export function filterError(filters: SearchFilters): string | null {
  for (const [label, min, max] of [
    ['Price', filters.minPrice, filters.maxPrice], ['THC', filters.minThc, filters.maxThc], ['CBD', filters.minCbd, filters.maxCbd],
  ] as const) {
    if (min !== undefined && max !== undefined && min > max) return `${label} minimum must not exceed its maximum.`
  }
  return null
}
export function searchParams(query: string, filters: SearchFilters): URLSearchParams {
  const params = new URLSearchParams()
  if (query.trim()) params.set('q', query.trim())
  if (filters.productType) params.set('product_type', filters.productType)
  for (const [field, key] of ranges) if (filters[field] !== undefined) params.set(key, String(filters[field]))
  if (filters.sortBy !== 'relevance') params.set('sort_by', filters.sortBy)
  return params
}
export function activeFilterCount(filters: SearchFilters) {
  return Number(Boolean(filters.productType)) + ranges.filter(([field]) => filters[field] !== undefined).length
}
