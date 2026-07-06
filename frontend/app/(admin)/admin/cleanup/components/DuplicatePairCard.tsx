'use client'

import React from 'react'
import { ScraperFlag, PairProduct } from '../hooks/useCleanupSession'

interface DuplicatePairCardProps {
  flag: ScraperFlag
  selected?: boolean
  winnerId: string | null
  loading?: boolean
  onToggleSelect: (flagId: string) => void
  onPickWinner: (flagId: string, productId: string) => void
  onMerge: (flag: ScraperFlag, winnerId: string) => Promise<void>
  onDismiss: (flagId: string) => Promise<void>
}

/**
 * Side-by-side review card for a duplicate_pair flag. The admin picks the
 * record to KEEP (winner, either side), then merges the other into it.
 */
export function DuplicatePairCard({
  flag,
  selected,
  winnerId,
  loading,
  onToggleSelect,
  onPickWinner,
  onMerge,
  onDismiss,
}: DuplicatePairCardProps) {
  const a = flag.duplicate_pair?.product_a
  const b = flag.duplicate_pair?.product_b
  const pct = Math.round(flag.confidence_score * 100)
  const sameDispensary = (flag.issue_tags || []).includes('same_dispensary_pair')

  if (!a || !b) {
    // One side was deleted since the scan — nothing to compare
    return (
      <div className="bg-white rounded-lg shadow p-5 flex items-center justify-between">
        <p className="text-sm text-gray-500">
          One of the products in this pair no longer exists.
        </p>
        <button
          onClick={() => onDismiss(flag.id)}
          disabled={loading}
          className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-600 rounded disabled:opacity-50"
        >
          Dismiss
        </button>
      </div>
    )
  }

  const fieldsDiffer = (x: string | null | undefined, y: string | null | undefined) =>
    (x || '').toLowerCase().trim() !== (y || '').toLowerCase().trim()

  return (
    <div className="bg-white rounded-lg shadow p-5 relative">
      {/* Checkbox for bulk selection */}
      <div className="absolute top-3 right-3">
        <input
          type="checkbox"
          checked={selected || false}
          onChange={() => onToggleSelect(flag.id)}
          className="w-5 h-5 rounded border-gray-300 text-cannabis-600 focus:ring-cannabis-500 cursor-pointer"
        />
      </div>

      {/* Header badges */}
      <div className="flex items-center gap-2 mb-3 flex-wrap pr-8">
        <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
          pct >= 80 ? 'bg-orange-100 text-orange-800' :
          pct >= 70 ? 'bg-yellow-100 text-yellow-800' :
          'bg-gray-100 text-gray-600'
        }`}>
          {pct}% similar
        </span>
        {flag.original_category && (
          <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded capitalize">
            {flag.original_category}
          </span>
        )}
        {sameDispensary && (
          <span className="text-xs font-medium text-yellow-700 bg-yellow-100 px-2 py-0.5 rounded">
            Same Dispensary
          </span>
        )}
      </div>

      {/* Side-by-side columns */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <PairColumn
          product={a}
          other={b}
          isWinner={winnerId === a.id}
          disabled={!!loading}
          onPick={() => onPickWinner(flag.id, a.id)}
          fieldsDiffer={fieldsDiffer}
        />
        <PairColumn
          product={b}
          other={a}
          isWinner={winnerId === b.id}
          disabled={!!loading}
          onPick={() => onPickWinner(flag.id, b.id)}
          fieldsDiffer={fieldsDiffer}
        />
      </div>

      {/* Actions */}
      <div className="flex gap-2 items-center">
        <button
          onClick={() => winnerId && onMerge(flag, winnerId)}
          disabled={loading || !winnerId}
          title={!winnerId ? 'Pick the record to keep first' : undefined}
          className="flex-1 bg-cannabis-600 hover:bg-cannabis-700 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '...' : winnerId ? 'Merge into Winner' : 'Merge (pick a winner first)'}
        </button>
        <button
          onClick={() => onDismiss(flag.id)}
          disabled={loading}
          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md font-medium text-sm transition-colors disabled:opacity-50"
        >
          Not Duplicates
        </button>
      </div>
    </div>
  )
}

function PairColumn({
  product,
  other,
  isWinner,
  disabled,
  onPick,
  fieldsDiffer,
}: {
  product: PairProduct
  other: PairProduct
  isWinner: boolean
  disabled: boolean
  onPick: () => void
  fieldsDiffer: (x: string | null | undefined, y: string | null | undefined) => boolean
}) {
  return (
    <button
      type="button"
      onClick={onPick}
      disabled={disabled}
      className={`text-left rounded-lg border-2 p-3 transition-colors ${
        isWinner
          ? 'border-cannabis-500 bg-cannabis-50'
          : 'border-gray-200 hover:border-gray-300 bg-white'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-4 h-4 rounded-full border-2 shrink-0 flex items-center justify-center ${
          isWinner ? 'border-cannabis-600 bg-cannabis-600' : 'border-gray-300'
        }`}>
          {isWinner && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
        </span>
        <span className={`text-xs font-semibold ${isWinner ? 'text-cannabis-700' : 'text-gray-400'}`}>
          {isWinner ? 'KEEP THIS ONE' : 'Click to keep'}
        </span>
      </div>

      <p className="font-bold text-gray-900 text-sm mb-1">{product.name}</p>

      <div className="space-y-0.5 text-xs">
        <PairField label="Brand" value={product.brand} differs={fieldsDiffer(product.brand, other.brand)} />
        <PairField label="Type" value={product.product_type} differs={fieldsDiffer(product.product_type, other.product_type)} />
        <PairField
          label="THC"
          value={product.thc_percentage != null ? `${product.thc_percentage}%` : null}
          differs={product.thc_percentage !== other.thc_percentage}
        />
        <PairField
          label="Weights"
          value={product.weights.length > 0 ? product.weights.join(', ') : null}
          differs={product.weights.join(',') !== other.weights.join(',')}
        />
      </div>

      {/* Dispensary chips with source links */}
      {product.dispensaries.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {product.dispensaries.map((d) =>
            d.url ? (
              <a
                key={d.name}
                href={d.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs hover:bg-blue-100 hover:underline"
                title={`Open on ${d.name} website${d.price != null ? ` — $${d.price}` : ''}`}
              >
                {d.name}{d.price != null ? ` $${d.price}` : ''} ↗
              </a>
            ) : (
              <span key={d.name} className="px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">
                {d.name}{d.price != null ? ` $${d.price}` : ''}
              </span>
            )
          )}
        </div>
      )}
    </button>
  )
}

function PairField({ label, value, differs }: { label: string; value: string | null; differs: boolean }) {
  return (
    <div className={`flex gap-1 px-1 -mx-1 rounded ${differs && value ? 'bg-yellow-50' : ''}`}>
      <span className="text-gray-400 w-14 shrink-0">{label}:</span>
      <span className="text-gray-800 font-medium truncate">{value || '—'}</span>
    </div>
  )
}
