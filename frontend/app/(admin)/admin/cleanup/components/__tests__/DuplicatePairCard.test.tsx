import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { DuplicatePairCard } from '../DuplicatePairCard'
import { ScraperFlag, PairProduct } from '../../hooks/useCleanupSession'

const productA: PairProduct = {
  id: 'prod-a',
  name: 'Blue Dream',
  product_type: 'flower',
  brand: 'Tryke',
  thc_percentage: 22,
  cbd_percentage: null,
  is_active: true,
  weights: ['3.5g'],
  dispensaries: [{ name: 'Disp One', url: 'https://one.example/p', price: 35 }],
}

const productB: PairProduct = {
  id: 'prod-b',
  name: 'Blue Dream Flower',
  product_type: 'flower',
  brand: 'Tryke',
  thc_percentage: 21,
  cbd_percentage: null,
  is_active: true,
  weights: ['7g'],
  dispensaries: [{ name: 'Disp Two', url: null, price: 60 }],
}

function makeFlag(overrides: Partial<ScraperFlag> = {}): ScraperFlag {
  return {
    id: 'flag-1',
    original_name: 'Blue Dream',
    original_thc: null,
    original_cbd: null,
    original_thc_content: null,
    original_cbd_content: null,
    original_weight: null,
    original_price: null,
    original_category: 'flower',
    original_url: null,
    brand_name: 'Tryke',
    dispensary_id: null,
    dispensary_name: null,
    matched_product_id: 'prod-a',
    secondary_product_id: 'prod-b',
    matched_product: null,
    duplicate_pair: { product_a: productA, product_b: productB },
    confidence_score: 0.75,
    confidence_percent: '75%',
    merge_reason: null,
    flag_type: 'duplicate_pair',
    status: 'pending',
    corrections: null,
    issue_tags: null,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    ...overrides,
  }
}

function renderCard(props: Partial<React.ComponentProps<typeof DuplicatePairCard>> = {}) {
  const defaults = {
    flag: makeFlag(),
    winnerId: null as string | null,
    onToggleSelect: jest.fn(),
    onPickWinner: jest.fn(),
    onMerge: jest.fn().mockResolvedValue(undefined),
    onDismiss: jest.fn().mockResolvedValue(undefined),
  }
  const merged = { ...defaults, ...props }
  return { ...render(<DuplicatePairCard {...merged} />), props: merged }
}

describe('DuplicatePairCard', () => {
  it('renders both products side by side', () => {
    renderCard()
    expect(screen.getByText('Blue Dream')).toBeInTheDocument()
    expect(screen.getByText('Blue Dream Flower')).toBeInTheDocument()
    expect(screen.getByText('75% similar')).toBeInTheDocument()
  })

  it('merge is disabled until a winner is picked', () => {
    renderCard()
    expect(
      screen.getByRole('button', { name: /Merge \(pick a winner first\)/i })
    ).toBeDisabled()
  })

  it('clicking a column picks that product as winner', () => {
    const { props } = renderCard()
    fireEvent.click(screen.getByText('Blue Dream Flower'))
    expect(props.onPickWinner).toHaveBeenCalledWith('flag-1', 'prod-b')
  })

  it('merge calls onMerge with the chosen winner (either direction)', () => {
    const { props } = renderCard({ winnerId: 'prod-b' })
    fireEvent.click(screen.getByRole('button', { name: /Merge into Winner/i }))
    expect(props.onMerge).toHaveBeenCalledWith(props.flag, 'prod-b')
  })

  it('Not Duplicates calls onDismiss with the flag id', () => {
    const { props } = renderCard()
    fireEvent.click(screen.getByRole('button', { name: /Not Duplicates/i }))
    expect(props.onDismiss).toHaveBeenCalledWith('flag-1')
  })

  it('shows dismiss-only fallback when a product side is missing', () => {
    const { props } = renderCard({
      flag: makeFlag({ duplicate_pair: { product_a: productA, product_b: null } }),
    })
    expect(screen.getByText(/no longer exists/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Dismiss/i }))
    expect(props.onDismiss).toHaveBeenCalledWith('flag-1')
  })
})
