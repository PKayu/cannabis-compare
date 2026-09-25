import { render, screen } from '@testing-library/react'
import PriceComparisonTable from '../PriceComparisonTable'
import type { ProductOffer } from '@/lib/product-contracts'

const offer: ProductOffer = {
  dispensary_id: 'shop', dispensary_name: 'Example shop', dispensary_location: null,
  dispensary_hours: null, dispensary_website: 'https://example.com', product_url: null,
  msrp: 30, deal_price: null, savings: null, savings_percentage: null, in_stock: true,
  promotion: null, last_updated: null,
}
test('does not advertise out-of-stock offers as lowest or link them externally', () => {
  render(<PriceComparisonTable prices={[{ ...offer, msrp: 1, in_stock: false }, { ...offer, dispensary_id: 'second', dispensary_name: 'Available shop' }]} weightGrams={3.5} />)
  expect(screen.getAllByText('Lowest listed in-stock price')).toHaveLength(1)
  expect(screen.getAllByRole('link', { name: /Visit dispensary website/ })).toHaveLength(1)
  expect(screen.getByText('Out of stock')).toBeInTheDocument()
  expect(screen.getByText('$8.57 / g')).toBeInTheDocument()
})
test('zero-price promotion is an estimate; missing URL is not a fake order action', () => {
  render(<PriceComparisonTable prices={[{ ...offer, deal_price: 0, dispensary_website: null }]} />)
  expect(screen.getByText('Possible promotion: $0.00')).toBeInTheDocument()
  expect(screen.getByText(/Confirm eligibility/)).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: /View at|Visit dispensary/ })).not.toBeInTheDocument()
})
