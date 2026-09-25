import type { ProductDetail, ProductOffer, SearchProduct, WeightGroup } from '../lib/product-contracts'

export const product: ProductDetail = {
  id: 'master', name: 'Blue Dream', brand: 'Example Grower', brand_id: 'brand', product_type: 'flower',
  thc_percentage: 22.5, cbd_percentage: null, is_master: true, normalization_confidence: null,
  created_at: null, updated_at: null, variants: [
    { id: 'small', weight: '3.5g', weight_grams: 3.5 },
    { id: 'large', weight: '7g', weight_grams: 7 },
    { id: 'missing', weight: '14g', weight_grams: 14 },
  ],
}
export const offer: ProductOffer = {
  dispensary_id: 'shop', dispensary_name: 'Example Dispensary', dispensary_location: 'Salt Lake City, UT',
  dispensary_hours: 'Hours not supplied', dispensary_website: 'https://example.com', product_url: 'https://example.com/product/blue-dream',
  msrp: 32, deal_price: 25.6, savings: 6.4, savings_percentage: 20, in_stock: true,
  promotion: { id: 'promo', title: 'Example promotion', description: null, discount_percentage: 20, discount_amount: null },
  last_updated: '2026-09-25T09:00:00Z',
}
export const groups: WeightGroup[] = [
  { variant_id: 'small', weight: '3.5g', weight_grams: 3.5, prices: [offer, { ...offer, dispensary_id: 'closed', dispensary_name: 'Unavailable Dispensary', msrp: 10, deal_price: null, in_stock: false }] },
  { variant_id: 'large', weight: '7g', weight_grams: 7, prices: [{ ...offer, msrp: 60, deal_price: null, product_url: null }] },
  { variant_id: 'unknown', weight: null, weight_grams: null, prices: [{ ...offer, dispensary_name: 'Unknown Size Dispensary', msrp: 20, deal_price: null, product_url: null, dispensary_website: null, last_updated: null }] },
]
export const results: SearchProduct[] = [
  { id: 'master', name: 'Blue Dream', brand: 'Example Grower', type: 'flower', thc: 22.5, cbd: null, min_price: 10, max_price: 60, dispensary_count: 2, available_weights: ['3.5g', '7g', '14g'], relevance_score: 1 },
  { id: 'partial', name: 'Blue Sky', brand: null, type: 'flower', thc: null, cbd: 0, min_price: 25, max_price: 25, dispensary_count: 1, available_weights: [], relevance_score: 0.5 },
]
