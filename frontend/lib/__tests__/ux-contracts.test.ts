import { comparisonGroups, offerDestination, potency, safeDispensaryUrl, updatedLabel, type ProductDetail, type ProductOffer } from '../product-contracts'
import { DEFAULT_FILTERS, filterError, readSearch, searchParams } from '../search-state'

const product: ProductDetail = {
  id: 'master', name: 'Example', brand: null, brand_id: null, product_type: 'flower',
  thc_percentage: null, cbd_percentage: 0, is_master: true, normalization_confidence: null,
  created_at: null, updated_at: null, variants: [
    { id: 'small', weight: '3.5g', weight_grams: 3.5 },
    { id: 'large', weight: '7g', weight_grams: 7 },
  ],
}
const offer: ProductOffer = {
  dispensary_id: 'shop', dispensary_name: 'Example shop', dispensary_location: null,
  dispensary_hours: null, dispensary_website: 'example.com', product_url: null,
  msrp: 30, deal_price: 0, savings: 30, savings_percentage: 100, in_stock: true,
  promotion: null, last_updated: null,
}

test('keeps unknown-size offers separate and retains variants with no prices', () => {
  const groups = comparisonGroups(product, [
    { variant_id: 'small', weight: '3.5g', weight_grams: 3.5, prices: [offer] },
    { variant_id: 'unknown', weight: null, weight_grams: null, prices: [offer] },
  ])
  expect(groups.map(group => [group.variant_id, group.prices.length])).toEqual([['small', 1], ['unknown', 1], ['large', 0]])
})
test.each(['javascript:alert(1)', 'data:text/html,test', '//evil.test', 'https://user:pass@evil.test', '/relative', 'example.com\\evil', 'not a url'])('rejects unsafe handoff %s', value => {
  expect(safeDispensaryUrl(value)).toBeNull()
})
test('uses explicit product URL, clearly labeled website fallback, or no action', () => {
  expect(offerDestination({ ...offer, product_url: 'https://example.com/product/1' })).toEqual({ href: 'https://example.com/product/1', label: 'View at dispensary' })
  expect(offerDestination(offer)).toEqual({ href: 'https://example.com/', label: 'Visit dispensary website' })
  expect(offerDestination({ ...offer, dispensary_website: null })).toBeNull()
})
test('does not confuse missing potency or timestamps with zero or freshness', () => {
  expect(potency(null)).toBe('Not reported')
  expect(potency(0)).toBe('0%')
  expect(updatedLabel('invalid')).toBe('Update time not reported')
})
test('round-trips deep-linked filters, zero values, query and server sorting', () => {
  const filters = { ...DEFAULT_FILTERS, productType: 'flower', minPrice: 0, maxPrice: 50, minThc: 15, maxCbd: 1, sortBy: 'price_low' as const }
  expect(readSearch(searchParams('  blue dream ', filters))).toEqual({ query: 'blue dream', filters })
  expect(filterError({ ...filters, minPrice: 60 })).toBe('Price minimum must not exceed its maximum.')
  expect(readSearch(new URLSearchParams('q=blue&min_thc=NaN&max_cbd=101')).filters).toEqual(DEFAULT_FILTERS)
})
