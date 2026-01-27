import React from 'react'

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

export default function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const handleChange = (field: string, value: any) => {
    onChange({
      ...filters,
      [field]: value === '' ? undefined : value
    })
  }

  const handleReset = () => {
    onChange({
      productType: '',
      minPrice: undefined,
      maxPrice: undefined,
      minThc: undefined,
      maxThc: undefined,
      minCbd: undefined,
      maxCbd: undefined,
      sortBy: 'relevance'
    })
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 sticky top-4">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        <button
          onClick={handleReset}
          className="text-sm text-cannabis-600 hover:text-cannabis-700 font-medium"
        >
          Reset
        </button>
      </div>

      {/* Product Type */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Product Type
        </label>
        <select
          value={filters.productType}
          onChange={(e) => handleChange('productType', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cannabis-500"
        >
          <option value="">All Types</option>
          <option value="flower">Flower</option>
          <option value="concentrate">Concentrate</option>
          <option value="edible">Edible</option>
          <option value="vaporizer">Vape</option>
          <option value="topical">Topical</option>
          <option value="tincture">Tincture</option>
          <option value="pre-roll">Pre-Roll</option>
        </select>
      </div>

      {/* Price Range */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Price Range
        </label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <input
              type="number"
              placeholder="Min"
              value={filters.minPrice ?? ''}
              onChange={(e) => handleChange('minPrice', e.target.value ? parseFloat(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cannabis-500"
              min="0"
              step="1"
            />
          </div>
          <div>
            <input
              type="number"
              placeholder="Max"
              value={filters.maxPrice ?? ''}
              onChange={(e) => handleChange('maxPrice', e.target.value ? parseFloat(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cannabis-500"
              min="0"
              step="1"
            />
          </div>
        </div>
      </div>

      {/* THC Percentage */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          THC %
        </label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <input
              type="number"
              placeholder="Min"
              value={filters.minThc ?? ''}
              onChange={(e) => handleChange('minThc', e.target.value ? parseFloat(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cannabis-500"
              min="0"
              max="100"
              step="0.1"
            />
          </div>
          <div>
            <input
              type="number"
              placeholder="Max"
              value={filters.maxThc ?? ''}
              onChange={(e) => handleChange('maxThc', e.target.value ? parseFloat(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cannabis-500"
              min="0"
              max="100"
              step="0.1"
            />
          </div>
        </div>
      </div>

      {/* CBD Percentage */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          CBD %
        </label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <input
              type="number"
              placeholder="Min"
              value={filters.minCbd ?? ''}
              onChange={(e) => handleChange('minCbd', e.target.value ? parseFloat(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cannabis-500"
              min="0"
              max="100"
              step="0.1"
            />
          </div>
          <div>
            <input
              type="number"
              placeholder="Max"
              value={filters.maxCbd ?? ''}
              onChange={(e) => handleChange('maxCbd', e.target.value ? parseFloat(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cannabis-500"
              min="0"
              max="100"
              step="0.1"
            />
          </div>
        </div>
      </div>

      {/* Sort By */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Sort By
        </label>
        <div className="space-y-2">
          {[
            { value: 'relevance', label: 'Relevance' },
            { value: 'price_low', label: 'Price: Low to High' },
            { value: 'price_high', label: 'Price: High to Low' },
            { value: 'thc', label: 'THC: High to Low' },
            { value: 'cbd', label: 'CBD: High to Low' }
          ].map((option) => (
            <label key={option.value} className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="sortBy"
                value={option.value}
                checked={filters.sortBy === option.value}
                onChange={(e) => handleChange('sortBy', e.target.value)}
                className="h-4 w-4 text-cannabis-600 focus:ring-cannabis-500 border-gray-300"
              />
              <span className="ml-2 text-sm text-gray-700">{option.label}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}
