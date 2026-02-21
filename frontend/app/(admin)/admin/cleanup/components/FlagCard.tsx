'use client'

import React, { useState, useEffect, useRef } from 'react'
import { ScraperFlag, EditableFields } from '../hooks/useCleanupSession'

const CATEGORY_OPTIONS = [
  'flower', 'concentrate', 'edible', 'vaporizer',
  'topical', 'tincture', 'pre-roll', 'other',
]

// --- Issue Tag Definitions ---

interface IssueTagDef {
  id: string
  label: string
  detect: (flag: ScraperFlag) => boolean
  apply: (values: Partial<EditableFields>, flag: ScraperFlag) => Partial<EditableFields> & { _highlightMissing?: boolean; _focusCategory?: boolean }
}

const WEIGHT_PATTERNS = [
  // Parenthesized: "Blue Dream (3.5g)"
  /\s*\((\d+(?:\.\d+)?\s*(?:g|gram|grams|oz|ounce|mg|milligram|milligrams|ml))\)\s*$/i,
  // Suffix: "Blue Dream 3.5g"
  /\s+(\d+(?:\.\d+)?\s*(?:g|gram|grams|oz|ounce|mg|milligram|milligrams))\s*$/i,
  // Fractional ounce: "Blue Dream 1/8 oz"
  /\s+(\d+\s*\/\s*\d+\s*(?:oz|ounce))\s*$/i,
]

const ISSUE_TAGS: IssueTagDef[] = [
  {
    id: 'weight_in_name',
    label: 'Weight in Name',
    detect: (flag) => /\d+(?:\.\d+)?\s*(?:g|oz|mg|gram|ounce)\b/i.test(flag.original_name),
    apply: (values) => {
      const name = values.name || ''
      for (const pattern of WEIGHT_PATTERNS) {
        const match = name.match(pattern)
        if (match) {
          return {
            name: name.replace(pattern, '').trim(),
            weight: match[1].trim(),
          }
        }
      }
      return {}
    },
  },
  {
    id: 'garbage_in_name',
    label: 'Junk in Name',
    detect: (flag) => /[<>&]|&[a-z]+;|\s{2,}|[^\x20-\x7E]/.test(flag.original_name),
    apply: (values) => {
      let cleaned = values.name || ''
      cleaned = cleaned.replace(/<[^>]*>/g, '')
      cleaned = cleaned.replace(/&[a-z]+;/gi, ' ')
      cleaned = cleaned.replace(/[^\x20-\x7E]/g, '')
      cleaned = cleaned.replace(/\s+/g, ' ').trim()
      return { name: cleaned }
    },
  },
  {
    id: 'missing_fields',
    label: 'Missing Fields',
    detect: (flag) => !flag.original_weight || !flag.original_price || !flag.original_category || flag.original_thc === null,
    apply: () => ({ _highlightMissing: true }),
  },
  {
    id: 'wrong_category',
    label: 'Wrong Category',
    detect: () => false,
    apply: () => ({ _focusCategory: true }),
  },
]

// --- Component Props ---

interface MatchedProductEdits {
  name?: string
  brand?: string
}

export type FlagCardTabMode = 'priority' | 'cleanup' | 'duplicates' | 'auto_linked' | 'all'

interface FlagCardProps {
  flag: ScraperFlag
  selected?: boolean
  tabMode?: FlagCardTabMode
  onToggleSelect?: (flagId: string) => void
  onApprove: (
    flagId: string,
    edits?: Partial<EditableFields>,
    notes?: string,
    issueTags?: string[],
    matchedEdits?: MatchedProductEdits
  ) => Promise<void>
  onReject: (flagId: string, edits?: Partial<EditableFields>, notes?: string, issueTags?: string[]) => Promise<void>
  onDismiss: (flagId: string, notes?: string, issueTags?: string[]) => Promise<void>
  onMergeDuplicate?: (flagId: string, keptProductId: string, notes?: string) => Promise<void>
}

export function FlagCard({ flag, selected, tabMode = 'all', onToggleSelect, onApprove, onReject, onDismiss, onMergeDuplicate }: FlagCardProps) {
  const [editing, setEditing] = useState<Record<string, boolean>>({})
  const [editValues, setEditValues] = useState<Partial<EditableFields>>({})
  const [activeTags, setActiveTags] = useState<string[]>([])
  const [tagSnapshots, setTagSnapshots] = useState<Record<string, string>>({})
  const [highlightMissing, setHighlightMissing] = useState(false)
  const [showNotes, setShowNotes] = useState(false)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [matchedEditing, setMatchedEditing] = useState<Record<string, boolean>>({})
  const [matchedEditValues, setMatchedEditValues] = useState<MatchedProductEdits>({})
  const categoryRef = useRef<HTMLSelectElement>(null)

  // Initialize edit values from flag data
  useEffect(() => {
    setEditValues({
      name: flag.original_name || '',
      brand_name: flag.brand_name || '',
      product_type: flag.original_category || '',
      thc_percentage: flag.original_thc?.toString() || '',
      cbd_percentage: flag.original_cbd?.toString() || '',
      weight: flag.original_weight || '',
      price: flag.original_price?.toString() || '',
    })
    setEditing({})
    setActiveTags([])
    setTagSnapshots({})
    setHighlightMissing(false)
    setNotes('')
    setShowNotes(false)
    setMatchedEditing({})
    setMatchedEditValues({})
  }, [flag.id])

  // Compute changed edits (only fields that differ from original)
  const getChangedEdits = (): Partial<EditableFields> | undefined => {
    const edits: Partial<EditableFields> = {}
    let hasChanges = false
    if (editValues.name !== (flag.original_name || '')) { edits.name = editValues.name; hasChanges = true }
    if (editValues.brand_name !== (flag.brand_name || '')) { edits.brand_name = editValues.brand_name; hasChanges = true }
    if (editValues.product_type !== (flag.original_category || '')) { edits.product_type = editValues.product_type; hasChanges = true }
    if (editValues.thc_percentage !== (flag.original_thc?.toString() || '')) { edits.thc_percentage = editValues.thc_percentage; hasChanges = true }
    if (editValues.cbd_percentage !== (flag.original_cbd?.toString() || '')) { edits.cbd_percentage = editValues.cbd_percentage; hasChanges = true }
    if (editValues.weight !== (flag.original_weight || '')) { edits.weight = editValues.weight; hasChanges = true }
    if (editValues.price !== (flag.original_price?.toString() || '')) { edits.price = editValues.price; hasChanges = true }
    return hasChanges ? edits : undefined
  }

  const handleApprove = async () => {
    setLoading(true)
    try {
      await onApprove(
        flag.id,
        getChangedEdits(),
        notes || undefined,
        activeTags.length > 0 ? activeTags : undefined,
        getMatchedEditsPayload()
      )
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async () => {
    setLoading(true)
    try {
      await onReject(flag.id, getChangedEdits(), notes || undefined, activeTags.length > 0 ? activeTags : undefined)
    } finally {
      setLoading(false)
    }
  }

  const handleDismiss = async () => {
    setLoading(true)
    try {
      await onDismiss(flag.id, notes || undefined, activeTags.length > 0 ? activeTags : undefined)
    } finally {
      setLoading(false)
    }
  }

  const toggleEditAll = () => {
    const allEditing = Object.values(editing).some(v => v)
    if (allEditing) {
      setEditing({})
    } else {
      setEditing({
        name: true, brand_name: true, product_type: true,
        thc_percentage: true, cbd_percentage: true, weight: true, price: true,
      })
    }
  }

  // Issue tag toggle with smart actions
  const handleTagToggle = (tag: IssueTagDef) => {
    if (activeTags.includes(tag.id)) {
      // Deactivate: restore snapshot
      const snapshot = tagSnapshots[tag.id]
      if (snapshot) {
        setEditValues(prev => ({ ...prev, ...JSON.parse(snapshot) }))
      }
      setActiveTags(prev => prev.filter(t => t !== tag.id))
      if (tag.id === 'missing_fields') setHighlightMissing(false)
    } else {
      // Activate: snapshot current, apply changes
      const changes = tag.apply(editValues, flag)

      // Save snapshot of fields that will change
      const fieldsToSnapshot: Record<string, string> = {}
      for (const key of Object.keys(changes)) {
        if (!key.startsWith('_')) {
          fieldsToSnapshot[key] = (editValues as Record<string, string>)[key] || ''
        }
      }
      setTagSnapshots(prev => ({ ...prev, [tag.id]: JSON.stringify(fieldsToSnapshot) }))

      // Apply non-sentinel changes
      const realChanges: Partial<EditableFields> = {}
      for (const [k, v] of Object.entries(changes)) {
        if (!k.startsWith('_')) {
          (realChanges as Record<string, string>)[k] = v as string
        }
      }
      if (Object.keys(realChanges).length > 0) {
        setEditValues(prev => ({ ...prev, ...realChanges }))
        // Auto-open editing on changed fields
        const newEditing: Record<string, boolean> = {}
        for (const key of Object.keys(realChanges)) {
          newEditing[key] = true
        }
        setEditing(prev => ({ ...prev, ...newEditing }))
      }

      // Handle sentinels
      if (changes._highlightMissing) {
        setHighlightMissing(true)
        const missing: Record<string, boolean> = {}
        if (!editValues.weight) missing.weight = true
        if (!editValues.price) missing.price = true
        if (!editValues.product_type) missing.product_type = true
        if (!editValues.thc_percentage) missing.thc_percentage = true
        setEditing(prev => ({ ...prev, ...missing }))
      }
      if (changes._focusCategory) {
        setEditing(prev => ({ ...prev, product_type: true }))
        setTimeout(() => categoryRef.current?.focus(), 50)
      }

      setActiveTags(prev => [...prev, tag.id])
    }
  }

  const updateField = (field: keyof EditableFields, value: string) => {
    setEditValues(prev => ({ ...prev, [field]: value }))
  }

  const isFieldMissing = (field: string) => {
    return highlightMissing && !(editValues as Record<string, string>)[field]
  }

  const hasEdits = !!getChangedEdits()

  const getMatchedEditsPayload = (): MatchedProductEdits | undefined => {
    const edits: MatchedProductEdits = {}
    let hasChanges = false
    if (matchedEditValues.name !== undefined && matchedEditValues.name !== (flag.matched_product?.name || '')) {
      edits.name = matchedEditValues.name; hasChanges = true
    }
    if (matchedEditValues.brand !== undefined && matchedEditValues.brand !== (flag.matched_product?.brand || '')) {
      edits.brand = matchedEditValues.brand; hasChanges = true
    }
    return hasChanges ? edits : undefined
  }

  const hasMatchedEdits = !!getMatchedEditsPayload()

  return (
    <div className="bg-white rounded-lg shadow p-5 relative">
      {/* Checkbox for bulk selection */}
      {onToggleSelect && (
        <div className="absolute top-3 right-3">
          <input
            type="checkbox"
            checked={selected || false}
            onChange={() => onToggleSelect(flag.id)}
            className="w-5 h-5 rounded border-gray-300 text-cannabis-600 focus:ring-cannabis-500 cursor-pointer"
          />
        </div>
      )}

      {/* Header Row */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0 pr-8">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            {flag.dispensary_name && (
              <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                {flag.dispensary_name}
              </span>
            )}

            {/* Match Type Badge */}
            {(flag as any).match_type === 'cross_dispensary' && (
              <span className="text-xs font-medium text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                Cross-Dispensary Match
              </span>
            )}
            {(flag as any).match_type === 'same_dispensary' && (
              <span className="text-xs font-medium text-yellow-700 bg-yellow-100 px-2 py-0.5 rounded">
                Same Dispensary
              </span>
            )}

            {/* Confidence Score */}
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
              flag.confidence_score >= 0.9
                ? 'bg-green-100 text-green-800'
                : flag.confidence_score >= 0.6
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {flag.confidence_percent || `${Math.round(flag.confidence_score * 100)}%`}
            </span>

            {/* Data Quality Indicator */}
            {(flag as any).data_quality === 'poor' && (
              <span className="text-xs font-medium text-red-700 bg-red-100 px-2 py-0.5 rounded flex items-center gap-1">
                ⚠️ Poor Quality
              </span>
            )}
            {(flag as any).data_quality === 'fair' && (
              <span className="text-xs font-medium text-orange-700 bg-orange-100 px-2 py-0.5 rounded flex items-center gap-1">
                ⚠️ Needs Review
              </span>
            )}
          </div>
          {/* Editable Name */}
          {editing.name ? (
            <input
              type="text"
              value={editValues.name || ''}
              onChange={(e) => updateField('name', e.target.value)}
              onBlur={() => setEditing(prev => ({ ...prev, name: false }))}
              className="w-full text-lg font-bold text-gray-900 border border-gray-300 rounded px-2 py-1 focus:ring-cannabis-500 focus:border-cannabis-500"
              autoFocus
            />
          ) : (
            <h3
              className="font-bold text-lg text-gray-900 cursor-pointer group flex items-center gap-1"
              onClick={() => setEditing(prev => ({ ...prev, name: true }))}
            >
              <span className={editValues.name !== (flag.original_name || '') ? 'text-cannabis-700' : ''}>
                {editValues.name || flag.original_name}
              </span>
              <PencilIcon />
            </h3>
          )}
        </div>
        <div className="flex items-center gap-2 ml-3 shrink-0">
          <button
            onClick={toggleEditAll}
            className="text-xs px-2 py-1 rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
          >
            {Object.values(editing).some(v => v) ? 'Done Editing' : 'Edit All'}
          </button>
        </div>
      </div>

      {/* Source URL - always visible */}
      <div className="mb-3">
        {flag.original_url ? (
          <a
            href={flag.original_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-cannabis-600 hover:text-cannabis-700 underline"
          >
            View Source Product Page
            <svg className="w-3 h-3 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        ) : (
          <span className="text-sm text-gray-400 italic">No source URL available</span>
        )}
      </div>

      {/* Editable Fields Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
        <EditableField
          label="Brand"
          value={editValues.brand_name || ''}
          original={flag.brand_name || ''}
          isEditing={!!editing.brand_name}
          isMissing={isFieldMissing('brand_name')}
          onEdit={() => setEditing(prev => ({ ...prev, brand_name: true }))}
          onBlur={() => setEditing(prev => ({ ...prev, brand_name: false }))}
          onChange={(v) => updateField('brand_name', v)}
        />
        <EditableSelectField
          label="Category"
          value={editValues.product_type || ''}
          original={flag.original_category || ''}
          options={CATEGORY_OPTIONS}
          isEditing={!!editing.product_type}
          isMissing={isFieldMissing('product_type')}
          onEdit={() => setEditing(prev => ({ ...prev, product_type: true }))}
          onBlur={() => setEditing(prev => ({ ...prev, product_type: false }))}
          onChange={(v) => updateField('product_type', v)}
          selectRef={categoryRef}
        />
        <EditableField
          label="Weight"
          value={editValues.weight || ''}
          original={flag.original_weight || ''}
          isEditing={!!editing.weight}
          isMissing={isFieldMissing('weight')}
          onEdit={() => setEditing(prev => ({ ...prev, weight: true }))}
          onBlur={() => setEditing(prev => ({ ...prev, weight: false }))}
          onChange={(v) => updateField('weight', v)}
        />
        <EditableField
          label="Price"
          value={editValues.price || ''}
          original={flag.original_price?.toString() || ''}
          isEditing={!!editing.price}
          isMissing={isFieldMissing('price')}
          onEdit={() => setEditing(prev => ({ ...prev, price: true }))}
          onBlur={() => setEditing(prev => ({ ...prev, price: false }))}
          onChange={(v) => updateField('price', v)}
          prefix="$"
          type="number"
        />
        <EditableField
          label="THC"
          value={editValues.thc_percentage || ''}
          original={flag.original_thc_content || (flag.original_thc?.toString() || '')}
          isEditing={!!editing.thc_percentage}
          isMissing={isFieldMissing('thc_percentage')}
          onEdit={() => setEditing(prev => ({ ...prev, thc_percentage: true }))}
          onBlur={() => setEditing(prev => ({ ...prev, thc_percentage: false }))}
          onChange={(v) => updateField('thc_percentage', v)}
          type="text"
        />
        <EditableField
          label="CBD"
          value={editValues.cbd_percentage || ''}
          original={flag.original_cbd_content || (flag.original_cbd?.toString() || '')}
          isEditing={!!editing.cbd_percentage}
          isMissing={isFieldMissing('cbd_percentage')}
          onEdit={() => setEditing(prev => ({ ...prev, cbd_percentage: true }))}
          onBlur={() => setEditing(prev => ({ ...prev, cbd_percentage: false }))}
          onChange={(v) => updateField('cbd_percentage', v)}
          type="text"
        />
      </div>

      {/* Matched Product Comparison with inline editing */}
      {flag.matched_product && (
        <div className="bg-gray-50 rounded-md p-3 mb-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-semibold text-gray-500">
              Suggested Match ({flag.confidence_percent || `${Math.round(flag.confidence_score * 100)}%`})
            </p>
            <button
              onClick={() => setMatchedEditing(prev => Object.values(prev).some(v => v) ? ({} as Record<string, boolean>) : { name: true, brand: true })}
              className="text-xs px-2 py-0.5 rounded border border-gray-300 text-gray-500 hover:bg-gray-100"
            >
              {Object.values(matchedEditing).some(v => v) ? 'Done' : 'Edit Match'}
            </button>
          </div>
          <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
            {/* Matched product Name — editable */}
            <div className="col-span-2">
              <span className="text-xs text-gray-400">Matched Name:</span>
              {matchedEditing.name ? (
                <input
                  type="text"
                  value={matchedEditValues.name ?? (flag.matched_product.name || '')}
                  onChange={(e) => setMatchedEditValues(prev => ({ ...prev, name: e.target.value }))}
                  onBlur={() => setMatchedEditing(prev => ({ ...prev, name: false }))}
                  className="w-full mt-0.5 text-sm border border-gray-300 rounded px-2 py-0.5 focus:ring-cannabis-500 focus:border-cannabis-500"
                  autoFocus
                />
              ) : (
                <p
                  className={`cursor-pointer hover:bg-gray-100 rounded px-1 -mx-1 font-medium ${
                    matchedEditValues.name !== undefined && matchedEditValues.name !== flag.matched_product.name
                      ? 'text-cannabis-700'
                      : 'text-gray-800'
                  }`}
                  onClick={() => setMatchedEditing(prev => ({ ...prev, name: true }))}
                >
                  {matchedEditValues.name ?? flag.matched_product.name}
                </p>
              )}
            </div>
            {/* Matched product Brand — editable */}
            <div>
              <span className="text-xs text-gray-400">Brand:</span>
              {matchedEditing.brand ? (
                <input
                  type="text"
                  value={matchedEditValues.brand ?? (flag.matched_product.brand || '')}
                  onChange={(e) => setMatchedEditValues(prev => ({ ...prev, brand: e.target.value }))}
                  onBlur={() => setMatchedEditing(prev => ({ ...prev, brand: false }))}
                  className="w-full mt-0.5 text-sm border border-gray-300 rounded px-2 py-0.5 focus:ring-cannabis-500 focus:border-cannabis-500"
                />
              ) : (
                <p
                  className={`cursor-pointer hover:bg-gray-100 rounded px-1 -mx-1 ${
                    matchedEditValues.brand !== undefined && matchedEditValues.brand !== flag.matched_product.brand
                      ? 'text-cannabis-700'
                      : 'text-gray-700'
                  }`}
                  onClick={() => setMatchedEditing(prev => ({ ...prev, brand: true }))}
                >
                  {matchedEditValues.brand ?? (flag.matched_product.brand || '—')}
                </p>
              )}
            </div>
            {/* Read-only comparison fields */}
            <CompareField label="Type" scraped={editValues.product_type || ''} matched={flag.matched_product.product_type || ''} />
            <CompareField
              label="THC"
              scraped={flag.original_thc_content || (editValues.thc_percentage ? `${editValues.thc_percentage}%` : '')}
              matched={flag.matched_product.thc_percentage != null ? `${flag.matched_product.thc_percentage}%` : ''}
            />
            <CompareField
              label="CBD"
              scraped={flag.original_cbd_content || (editValues.cbd_percentage ? `${editValues.cbd_percentage}%` : '')}
              matched={flag.matched_product.cbd_percentage != null ? `${flag.matched_product.cbd_percentage}%` : ''}
            />
          </div>
          {flag.merge_reason && (
            <p className="text-xs text-gray-400 mt-2">{flag.merge_reason}</p>
          )}
        </div>
      )}

      {/* Issue Tags */}
      <div className="flex flex-wrap gap-2 mb-4">
        {ISSUE_TAGS.map(tag => {
          const isActive = activeTags.includes(tag.id)
          const isDetected = tag.detect(flag)
          return (
            <button
              key={tag.id}
              onClick={() => handleTagToggle(tag)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                isActive
                  ? 'bg-cannabis-100 border-cannabis-500 text-cannabis-800'
                  : isDetected
                  ? 'bg-yellow-50 border-yellow-300 text-yellow-700'
                  : 'bg-gray-50 border-gray-200 text-gray-500 hover:bg-gray-100'
              }`}
            >
              {tag.label}
              {isDetected && !isActive && ' (!)'}
            </button>
          )
        })}
      </div>

      {/* Notes */}
      {showNotes && (
        <div className="mb-4">
          <textarea
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-cannabis-500 focus:border-cannabis-500"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add notes about this decision..."
          />
        </div>
      )}

      {/* Action Buttons — rendered contextually by tab */}
      <div className="flex gap-2">
        {/* Priority Queue: full approve + new product + dismiss */}
        {(tabMode === 'priority' || tabMode === 'all') && (
          <>
            <button
              onClick={handleApprove}
              disabled={loading || (!flag.matched_product_id && !flag.matched_product?.id)}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={(!flag.matched_product_id && !flag.matched_product?.id) ? 'No suggested match — use New Product instead' : undefined}
            >
              {loading ? '...' : hasEdits || hasMatchedEdits ? 'Approve + Save Edits' : 'Approve'}
            </button>
            <button
              onClick={handleReject}
              disabled={loading}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50"
            >
              {loading ? '...' : hasEdits ? 'New Product + Save Edits' : 'New Product'}
            </button>
          </>
        )}

        {/* Needs Cleanup: only Save as New Product + Dismiss (no linking) */}
        {tabMode === 'cleanup' && (
          <button
            onClick={handleReject}
            disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50"
          >
            {loading ? '...' : hasEdits ? 'Save as New Product' : 'Save as New Product'}
          </button>
        )}

        {/* Duplicates: Keep This One + Not a Duplicate */}
        {tabMode === 'duplicates' && flag.matched_product_id && (
          <>
            <button
              onClick={() => onMergeDuplicate && onMergeDuplicate(flag.id, flag.matched_product_id!, notes || undefined)}
              disabled={loading || !onMergeDuplicate}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '...' : 'Keep Matched Product'}
            </button>
            <button
              onClick={handleApprove}
              disabled={loading || (!flag.matched_product_id && !flag.matched_product?.id)}
              className="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '...' : 'Keep Incoming'}
            </button>
          </>
        )}
        {tabMode === 'duplicates' && !flag.matched_product_id && (
          <button
            onClick={handleReject}
            disabled={loading}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50"
          >
            {loading ? '...' : 'Create as New Product'}
          </button>
        )}

        {/* Auto-Linked: read-only confirmation buttons */}
        {tabMode === 'auto_linked' && (
          <button
            onClick={handleDismiss}
            disabled={loading}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50"
          >
            {loading ? '...' : 'Looks Good ✓'}
          </button>
        )}

        {/* Dismiss always shown (except auto_linked where it's "Looks Good") */}
        {tabMode !== 'auto_linked' && (
          <button
            onClick={handleDismiss}
            disabled={loading}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md font-medium text-sm transition-colors disabled:opacity-50"
          >
            {tabMode === 'duplicates' ? 'Not a Duplicate' : 'Dismiss'}
          </button>
        )}

        <button
          onClick={() => setShowNotes(!showNotes)}
          className={`px-3 py-2 rounded-md text-sm transition-colors ${
            showNotes ? 'bg-gray-800 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
          }`}
          title="Toggle notes"
        >
          Notes
        </button>
      </div>
    </div>
  )
}

// --- Sub-components ---

function PencilIcon() {
  return (
    <svg className="w-3.5 h-3.5 text-gray-400 opacity-0 group-hover:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
    </svg>
  )
}

function EditableField({
  label, value, original, isEditing, isMissing, onEdit, onBlur, onChange,
  prefix, suffix, type = 'text',
}: {
  label: string; value: string; original: string;
  isEditing: boolean; isMissing: boolean;
  onEdit: () => void; onBlur: () => void; onChange: (v: string) => void;
  prefix?: string; suffix?: string; type?: string;
}) {
  const changed = value !== original
  const ringClass = isMissing ? 'ring-2 ring-yellow-300' : ''

  if (isEditing) {
    return (
      <div className={`${ringClass} rounded`}>
        <label className="text-xs text-gray-500 block mb-0.5">{label}</label>
        <div className="flex items-center">
          {prefix && <span className="text-gray-400 text-sm mr-1">{prefix}</span>}
          <input
            type={type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onBlur={onBlur}
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:ring-cannabis-500 focus:border-cannabis-500"
            autoFocus
          />
          {suffix && <span className="text-gray-400 text-sm ml-1">{suffix}</span>}
        </div>
      </div>
    )
  }

  return (
    <div
      className={`cursor-pointer group ${ringClass} rounded p-1 -m-1`}
      onClick={onEdit}
    >
      <span className="text-xs text-gray-500">{label}:</span>
      <span className={`ml-1 text-sm font-medium ${changed ? 'text-cannabis-700' : 'text-gray-900'}`}>
        {prefix}{value || <span className="text-gray-400">N/A</span>}{value && suffix}
      </span>
      <PencilIcon />
    </div>
  )
}

function EditableSelectField({
  label, value, original, options, isEditing, isMissing, onEdit, onBlur, onChange, selectRef,
}: {
  label: string; value: string; original: string; options: string[];
  isEditing: boolean; isMissing: boolean;
  onEdit: () => void; onBlur: () => void; onChange: (v: string) => void;
  selectRef?: React.Ref<HTMLSelectElement>;
}) {
  const changed = value !== original
  const ringClass = isMissing ? 'ring-2 ring-yellow-300' : ''

  if (isEditing) {
    return (
      <div className={`${ringClass} rounded`}>
        <label className="text-xs text-gray-500 block mb-0.5">{label}</label>
        <select
          ref={selectRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          className="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:ring-cannabis-500 focus:border-cannabis-500"
          autoFocus
        >
          <option value="">Select...</option>
          {options.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>
    )
  }

  return (
    <div
      className={`cursor-pointer group ${ringClass} rounded p-1 -m-1`}
      onClick={onEdit}
    >
      <span className="text-xs text-gray-500">{label}:</span>
      <span className={`ml-1 text-sm font-medium ${changed ? 'text-cannabis-700' : 'text-gray-900'}`}>
        {value || <span className="text-gray-400">N/A</span>}
      </span>
      <PencilIcon />
    </div>
  )
}

function CompareField({ label, scraped, matched }: { label: string; scraped: string; matched: string }) {
  const match = scraped.toLowerCase().trim() === matched.toLowerCase().trim()
  const bg = !scraped && !matched ? '' : match ? 'bg-green-50' : 'bg-yellow-50'
  return (
    <div className={`flex justify-between px-2 py-0.5 rounded ${bg}`}>
      <span className="text-gray-500 text-xs w-12">{label}:</span>
      <span className="text-xs font-medium text-gray-900 truncate">{matched || 'N/A'}</span>
    </div>
  )
}
