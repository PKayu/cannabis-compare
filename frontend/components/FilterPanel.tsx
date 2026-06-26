'use client'

import React, { useState } from 'react'
import { useToast } from '@/components/Toast'
import CannabisLeaf from '@/components/CannabisLeaf'

interface FilterPanelProps {
  filters: {
    productType: string
    minPrice: number | undefined
    maxPrice: number | undefined
    minThc: number | undefined
    maxThc: number | undefined
    minCbd: number | undefined
    maxCbd: number | undefined
    sortBy: string
  }
  onChange: (filters: any) => void
}

const PRODUCT_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'flower', label: 'Flower' },
  { value: 'concentrate', label: 'Concentrate' },
  { value: 'edible', label: 'Edible' },
  { value: 'vaporizer', label: 'Vape' },
  { value: 'topical', label: 'Topical' },
  { value: 'tincture', label: 'Tincture' },
  { value: 'pre-roll', label: 'Pre-Roll' },
  { value: 'hardware', label: 'Hardware' },
]

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'price_low', label: 'Price: Low → High' },
  { value: 'price_high', label: 'Price: High → Low' },
  { value: 'thc', label: 'THC: High → Low' },
  { value: 'cbd', label: 'CBD: High → Low' },
]

export default function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const { showToast } = useToast()
  const [isShaking, setIsShaking] = useState(false)

  const handleChange = (field: string, value: any) => {
    onChange({ ...filters, [field]: value === '' ? undefined : value })
  }

  const handleReset = () => {
    setIsShaking(true)
    setTimeout(() => setIsShaking(false), 500)
    onChange({
      productType: '',
      minPrice: undefined,
      maxPrice: undefined,
      minThc: undefined,
      maxThc: undefined,
      minCbd: undefined,
      maxCbd: undefined,
      sortBy: 'relevance',
    })
    showToast('Filters cleared!', 'info')
  }

  const inputClass = 'w-full px-3 py-2 bg-white border-2 border-groovy-ink rounded-xl font-body text-sm text-groovy-ink focus:outline-none focus:ring-2 focus:ring-groovy-amber'
  const labelClass = 'block font-display font-semibold text-sm text-groovy-ink mb-2'

  return (
    <div className="bg-groovy-cream border-2 border-groovy-ink rounded-2xl shadow-sticker p-6 sticky top-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-2">
          <CannabisLeaf size={20} color="#0D9488" rotate={-10} />
          <h2 className="font-display font-bold text-lg text-groovy-ink">Filters</h2>
        </div>
        <button
          onClick={handleReset}
          className={`font-display text-sm font-semibold text-groovy-amber hover:text-groovy-rust border-b border-groovy-amber transition-colors ${isShaking ? 'animate-shake' : ''}`}
        >
          Reset
        </button>
      </div>

      {/* Product Type — pill chips */}
      <div className="mb-6">
        <label className={labelClass}>Product Type</label>
        <div className="flex flex-wrap gap-1.5">
          {PRODUCT_TYPES.map((t) => (
            <button
              key={t.value}
              onClick={() => handleChange('productType', t.value)}
              className={`px-3 py-1 rounded-full text-xs font-display font-semibold border-2 transition-all duration-150 ${
                filters.productType === t.value
                  ? 'bg-groovy-teal text-white border-groovy-ink shadow-[2px_2px_0px_#1C1917]'
                  : 'bg-white text-groovy-ink border-groovy-ink hover:bg-amber-50'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Price Range */}
      <div className="mb-6">
        <label className={labelClass}>Price Range</label>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            placeholder="Min $"
            value={filters.minPrice ?? ''}
            onChange={(e) => handleChange('minPrice', e.target.value ? parseFloat(e.target.value) : undefined)}
            className={inputClass}
            min="0"
            step="1"
          />
          <input
            type="number"
            placeholder="Max $"
            value={filters.maxPrice ?? ''}
            onChange={(e) => handleChange('maxPrice', e.target.value ? parseFloat(e.target.value) : undefined)}
            className={inputClass}
            min="0"
            step="1"
          />
        </div>
      </div>

      {/* THC % */}
      <div className="mb-6">
        <label className={labelClass}>THC %</label>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            placeholder="Min"
            value={filters.minThc ?? ''}
            onChange={(e) => handleChange('minThc', e.target.value ? parseFloat(e.target.value) : undefined)}
            className={inputClass}
            min="0" max="100" step="0.1"
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.maxThc ?? ''}
            onChange={(e) => handleChange('maxThc', e.target.value ? parseFloat(e.target.value) : undefined)}
            className={inputClass}
            min="0" max="100" step="0.1"
          />
        </div>
      </div>

      {/* CBD % */}
      <div className="mb-6">
        <label className={labelClass}>CBD %</label>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            placeholder="Min"
            value={filters.minCbd ?? ''}
            onChange={(e) => handleChange('minCbd', e.target.value ? parseFloat(e.target.value) : undefined)}
            className={inputClass}
            min="0" max="100" step="0.1"
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.maxCbd ?? ''}
            onChange={(e) => handleChange('maxCbd', e.target.value ? parseFloat(e.target.value) : undefined)}
            className={inputClass}
            min="0" max="100" step="0.1"
          />
        </div>
      </div>

      {/* Sort By */}
      <div>
        <label className={labelClass}>Sort By</label>
        <div className="space-y-2">
          {SORT_OPTIONS.map((option) => (
            <label key={option.value} className="flex items-center gap-2.5 cursor-pointer group">
              <div className={`w-4 h-4 rounded-full border-2 border-groovy-ink flex items-center justify-center flex-shrink-0 transition-colors ${
                filters.sortBy === option.value ? 'bg-groovy-teal' : 'bg-white group-hover:bg-amber-50'
              }`}>
                {filters.sortBy === option.value && (
                  <div className="w-1.5 h-1.5 rounded-full bg-white" />
                )}
              </div>
              <input
                type="radio"
                name="sortBy"
                value={option.value}
                checked={filters.sortBy === option.value}
                onChange={(e) => handleChange('sortBy', e.target.value)}
                className="sr-only"
              />
              <span className="font-body text-sm text-groovy-ink">{option.label}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}
