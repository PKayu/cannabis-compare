'use client'

import React, { useState } from 'react'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/AuthContext'

interface ReviewFormProps {
  productId: string
  onSubmit?: () => void
  onCancel?: () => void
}

const medicalIntentions = [
  { value: 'pain', label: 'Pain Relief' },
  { value: 'insomnia', label: 'Sleep/Insomnia' },
  { value: 'anxiety', label: 'Anxiety' },
  { value: 'nausea', label: 'Nausea' },
  { value: 'spasms', label: 'Spasms' },
]

const moodIntentions = [
  { value: 'socializing', label: 'Socializing' },
  { value: 'creativity', label: 'Creativity' },
  { value: 'deep_relaxation', label: 'Deep Relaxation' },
  { value: 'focus', label: 'Focus' },
  { value: 'post_workout', label: 'Post-Workout Recovery' },
]

export default function ReviewForm({ productId, onSubmit, onCancel }: ReviewFormProps) {
  const { user, loading: authLoading } = useAuth()
  const [formData, setFormData] = useState({
    effects_rating: 3,
    taste_rating: 3,
    value_rating: 3,
    intention_type: 'medical',
    intention_tag: 'pain',
    batch_number: '',
    cultivation_date: '',
    comment: ''
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const intentionOptions = formData.intention_type === 'medical' ? medicalIntentions : moodIntentions

  // Show sign-in prompt if not authenticated
  if (!authLoading && !user) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
        <h3 className="text-xl font-bold mb-4 text-cannabis-800">Share Your Review</h3>
        <p className="text-gray-600 mb-4">Please sign in to leave a review.</p>
        <a
          href={`/auth/login?returnUrl=${encodeURIComponent(typeof window !== 'undefined' ? window.location.pathname : '')}`}
          className="inline-block px-4 py-2 bg-cannabis-600 text-white rounded hover:bg-cannabis-700 transition-colors font-semibold"
        >
          Sign In
        </a>
      </div>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      await api.post('/api/reviews', {
        product_id: productId,
        effects_rating: formData.effects_rating,
        taste_rating: formData.taste_rating,
        value_rating: formData.value_rating,
        intention_type: formData.intention_type,
        intention_tag: formData.intention_tag,
        batch_number: formData.batch_number || null,
        cultivation_date: formData.cultivation_date || null,
        comment: formData.comment || null
      })

      // Reset form
      setFormData({
        effects_rating: 3,
        taste_rating: 3,
        value_rating: 3,
        intention_type: 'medical',
        intention_tag: 'pain',
        batch_number: '',
        cultivation_date: '',
        comment: ''
      })

      if (onSubmit) onSubmit()
    } catch (err: any) {
      console.error('Failed to submit review:', err)

      // Handle unauthorized error - redirect to login
      if (err.response?.status === 401) {
        const returnUrl = encodeURIComponent(window.location.pathname)
        window.location.href = `/auth/login?returnUrl=${returnUrl}`
        return
      }

      setError(err.response?.data?.detail || 'Failed to submit review. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleIntentionTypeChange = (type: string) => {
    setFormData({
      ...formData,
      intention_type: type,
      intention_tag: type === 'medical' ? 'pain' : 'socializing'
    })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
      <h3 className="text-2xl font-bold mb-6 text-cannabis-800">Share Your Review</h3>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Star Ratings */}
      <div className="mb-8">
        <p className="font-bold mb-4 text-cannabis-800">How would you rate this product?</p>

        <RatingInput
          label="Effects"
          value={formData.effects_rating}
          onChange={(v) => setFormData({ ...formData, effects_rating: v })}
        />
        <RatingInput
          label="Taste"
          value={formData.taste_rating}
          onChange={(v) => setFormData({ ...formData, taste_rating: v })}
        />
        <RatingInput
          label="Value"
          value={formData.value_rating}
          onChange={(v) => setFormData({ ...formData, value_rating: v })}
        />
      </div>

      {/* Dual-Track Intention Selection */}
      <div className="mb-8 p-4 bg-cannabis-50 rounded-lg border border-cannabis-200">
        <p className="font-bold mb-4 text-cannabis-800">Why did you use this product?</p>

        <div className="mb-4">
          <label className="block font-semibold mb-2 text-gray-700">Use Type</label>
          <select
            value={formData.intention_type}
            onChange={(e) => handleIntentionTypeChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-cannabis-500"
          >
            <option value="medical">🏥 Medical</option>
            <option value="mood">😊 Mood/Wellness</option>
          </select>
        </div>

        <div>
          <label className="block font-semibold mb-2 text-gray-700">Specific Use</label>
          <select
            value={formData.intention_tag}
            onChange={(e) => setFormData({ ...formData, intention_tag: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-cannabis-500"
          >
            {intentionOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Batch Tracking (Optional) */}
      <div className="mb-8">
        <p className="font-bold mb-4 text-cannabis-800">Product Details <span className="text-sm text-gray-500 font-normal">(Optional)</span></p>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700">Batch Number</label>
            <input
              type="text"
              placeholder="e.g., BATCH-2024-001"
              value={formData.batch_number}
              onChange={(e) => setFormData({ ...formData, batch_number: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-cannabis-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700">Cultivation Date</label>
            <input
              type="date"
              value={formData.cultivation_date}
              onChange={(e) => setFormData({ ...formData, cultivation_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-cannabis-500"
            />
          </div>
        </div>
      </div>

      {/* Comment */}
      <div className="mb-6">
        <label className="block font-bold mb-2 text-cannabis-800">Your Thoughts</label>
        <textarea
          value={formData.comment}
          onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
          placeholder="Share your experience with this product..."
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-cannabis-500"
          rows={4}
          maxLength={1000}
        />
        <p className="text-sm text-gray-500 mt-1">{formData.comment.length}/1000 characters</p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 px-4 py-2 bg-cannabis-600 text-white rounded hover:bg-cannabis-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-semibold"
        >
          {loading ? 'Submitting...' : 'Submit Review'}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors font-semibold"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}

interface RatingInputProps {
  label: string
  value: number
  onChange: (value: number) => void
}

function RatingInput({ label, value, onChange }: RatingInputProps) {
  return (
    <div className="mb-4">
      <label className="block font-semibold mb-2 text-gray-700">{label}</label>
      <div className="flex gap-2">
        {[1, 2, 3, 4, 5].map((rating) => (
          <button
            key={rating}
            type="button"
            onClick={() => onChange(rating)}
            className={`w-12 h-12 rounded border-2 transition-all ${
              value >= rating
                ? 'border-cannabis-600 bg-cannabis-100 text-cannabis-700'
                : 'border-gray-300 bg-white text-gray-400 hover:border-cannabis-400'
            }`}
          >
            <span className="text-xl">{rating}★</span>
          </button>
        ))}
      </div>
    </div>
  )
}
