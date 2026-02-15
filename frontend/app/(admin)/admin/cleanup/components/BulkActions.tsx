'use client'

import React, { useState } from 'react'

interface BulkActionsProps {
  selectedFlagIds: string[]
  totalFlags: number
  onSelectAll: () => void
  onDeselectAll: () => void
  onBulkApprove: () => Promise<void>
  onBulkReject: () => Promise<void>
  onBulkDismiss: () => Promise<void>
}

export function BulkActions({
  selectedFlagIds,
  totalFlags,
  onSelectAll,
  onDeselectAll,
  onBulkApprove,
  onBulkReject,
  onBulkDismiss,
}: BulkActionsProps) {
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [confirmAction, setConfirmAction] = useState<'approve' | 'reject' | 'dismiss' | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  if (selectedFlagIds.length === 0) return null

  const handleActionClick = (action: 'approve' | 'reject' | 'dismiss') => {
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
              <p className="text-sm text-gray-500 mb-6">
                <strong>Note:</strong> Bulk operations do not support per-flag field edits.
                Use individual flag actions if you need to make corrections.
              </p>

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
                  className={`
                    px-4 py-2 text-white rounded-md shadow-sm disabled:opacity-50 transition-colors
                    ${confirmAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : ''}
                    ${confirmAction === 'reject' ? 'bg-red-600 hover:bg-red-700' : ''}
                    ${confirmAction === 'dismiss' ? 'bg-gray-600 hover:bg-gray-700' : ''}
                  `}
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
