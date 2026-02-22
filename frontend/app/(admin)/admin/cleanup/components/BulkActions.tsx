'use client'

import React, { useState } from 'react'
import { FilterTab } from './FilterTabs'

interface BulkActionsProps {
  selectedFlagIds: string[]
  totalFlags: number
  activeTab: FilterTab
  onSelectAll: () => void
  onDeselectAll: () => void
  onBulkApprove: () => Promise<void>
  onBulkReject: () => Promise<void>
  onBulkDismiss: () => Promise<void>
  onBulkClean?: () => Promise<void>
  onBulkDelete?: () => Promise<void>
}

export function BulkActions({
  selectedFlagIds,
  totalFlags,
  activeTab,
  onSelectAll,
  onDeselectAll,
  onBulkApprove,
  onBulkReject,
  onBulkDismiss,
  onBulkClean,
  onBulkDelete,
}: BulkActionsProps) {
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [confirmAction, setConfirmAction] = useState<'approve' | 'reject' | 'dismiss' | 'clean' | 'delete' | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  if (selectedFlagIds.length === 0) return null

  const handleActionClick = (action: typeof confirmAction) => {
    setConfirmAction(action)
    setShowConfirmModal(true)
  }

  const handleConfirm = async () => {
    setIsProcessing(true)
    try {
      if (confirmAction === 'approve') {
        await onBulkApprove()
      } else if (confirmAction === 'reject') {
        await onBulkReject()
      } else if (confirmAction === 'dismiss') {
        await onBulkDismiss()
      } else if (confirmAction === 'clean' && onBulkClean) {
        await onBulkClean()
      } else if (confirmAction === 'delete' && onBulkDelete) {
        await onBulkDelete()
      }
    } finally {
      setIsProcessing(false)
      setShowConfirmModal(false)
      setConfirmAction(null)
    }
  }

  const handleCancel = () => {
    setShowConfirmModal(false)
    setConfirmAction(null)
  }

  const getActionDescription = () => {
    switch (confirmAction) {
      case 'approve':
        return 'merge them with the matched products'
      case 'reject':
        return 'create new products for each flag'
      case 'dismiss':
        return 'dismiss them without creating products'
      case 'clean':
        return 'activate them with their current data (no edits applied)'
      case 'delete':
        return 'permanently delete the flagged products'
      default:
        return ''
    }
  }

  const getConfirmButtonClass = () => {
    switch (confirmAction) {
      case 'approve':
      case 'clean':
        return 'bg-green-600 hover:bg-green-700'
      case 'reject':
      case 'delete':
        return 'bg-red-600 hover:bg-red-700'
      case 'dismiss':
        return 'bg-gray-600 hover:bg-gray-700'
      default:
        return ''
    }
  }

  return (
    <>
      {/* Bulk Action Toolbar */}
      <div className="sticky top-0 z-10 bg-blue-50 border-b border-blue-200 px-4 py-3 flex items-center gap-3 shadow-sm">
        <div className="flex items-center gap-2 text-sm font-medium text-blue-900">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          <span>{selectedFlagIds.length} selected</span>
        </div>

        <button
          onClick={onSelectAll}
          className="text-sm text-blue-600 hover:text-blue-700 hover:underline"
        >
          Select All ({totalFlags})
        </button>

        <button
          onClick={onDeselectAll}
          className="text-sm text-blue-600 hover:text-blue-700 hover:underline"
        >
          Clear
        </button>

        <div className="flex-1" />

        {/* Data Cleanup tab: Activate All + Delete All */}
        {activeTab === 'data_cleanup' && (
          <>
            <button
              onClick={() => handleActionClick('clean')}
              disabled={isProcessing || !onBulkClean}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white text-sm font-medium rounded-md shadow-sm transition-colors"
            >
              Activate All
            </button>
            <button
              onClick={() => handleActionClick('delete')}
              disabled={isProcessing || !onBulkDelete}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white text-sm font-medium rounded-md shadow-sm transition-colors"
            >
              Delete All
            </button>
          </>
        )}

        {/* Legacy Review tab: Approve All + Reject All + Dismiss All */}
        {(activeTab === 'legacy_review' || activeTab === 'all') && (
          <>
            <button
              onClick={() => handleActionClick('approve')}
              disabled={isProcessing}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white text-sm font-medium rounded-md shadow-sm transition-colors"
            >
              Approve All
            </button>
            <button
              onClick={() => handleActionClick('reject')}
              disabled={isProcessing}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white text-sm font-medium rounded-md shadow-sm transition-colors"
            >
              Reject All
            </button>
            <button
              onClick={() => handleActionClick('dismiss')}
              disabled={isProcessing}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white text-sm font-medium rounded-md shadow-sm transition-colors"
            >
              Dismiss All
            </button>
          </>
        )}

        {/* Auto-Linked tab: Dismiss All */}
        {activeTab === 'auto_linked' && (
          <button
            onClick={() => handleActionClick('dismiss')}
            disabled={isProcessing}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white text-sm font-medium rounded-md shadow-sm transition-colors"
          >
            Mark All OK
          </button>
        )}
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Confirm Bulk Action
              </h3>
              <p className="text-gray-600 mb-4">
                You are about to <strong>{confirmAction}</strong> {selectedFlagIds.length} flag{selectedFlagIds.length > 1 ? 's' : ''}.
                This will {getActionDescription()}.
              </p>
              {confirmAction === 'clean' && (
                <p className="text-sm text-yellow-600 mb-4">
                  <strong>Note:</strong> Bulk activate uses the current data without per-flag edits. For corrections, use individual cards.
                </p>
              )}
              {confirmAction === 'delete' && (
                <p className="text-sm text-red-600 mb-4">
                  <strong>Warning:</strong> This permanently deletes the flagged products and cannot be undone.
                </p>
              )}

              <div className="flex gap-3 justify-end">
                <button
                  onClick={handleCancel}
                  disabled={isProcessing}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={isProcessing}
                  className={`px-4 py-2 text-white rounded-md shadow-sm disabled:opacity-50 transition-colors ${getConfirmButtonClass()}`}
                >
                  {isProcessing ? 'Processing...' : `Confirm ${confirmAction}`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
