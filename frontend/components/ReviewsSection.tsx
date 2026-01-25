'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import ReviewForm from './ReviewForm'

interface ReviewsSectionProps {
  productId: string
}

interface Review {
  id: string
  rating: number
  effects_rating: number | null
  taste_rating: number | null
  value_rating: number | null
  intention_type: string | null
  intention_tag: string | null
  comment: string | null
  upvotes: number
  username: string
  created_at: string
  updated_at: string
}

export default function ReviewsSection({ productId }: ReviewsSectionProps) {
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [filterIntention, setFilterIntention] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState('recent')

  useEffect(() => {
    loadReviews()
  }, [filterIntention, sortBy, productId])

  const loadReviews = async () => {
    try {
      setLoading(true)
      const params: any = { sort_by: sortBy }
      if (filterIntention) {
        params.intention_tag = filterIntention
      }

      const response = await api.get(`/api/reviews/product/${productId}`, { params })
      setReviews(response.data)
    } catch (error) {
      console.error('Failed to load reviews:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleReviewSubmitted = () => {
    setShowForm(false)
    loadReviews() // Refresh reviews list
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold text-cannabis-800">Community Reviews</h3>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700 transition-colors font-semibold"
          >
            Write a Review
          </button>
        )}
      </div>

      {/* Review Form */}
      {showForm && (
        <div className="mb-8">
          <ReviewForm
            productId={productId}
            onSubmit={handleReviewSubmitted}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {/* Filters and Sorting */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <label className="block text-sm font-semibold mb-2 text-gray-700">Filter by Use Case</label>
          <select
            value={filterIntention || ''}
            onChange={(e) => setFilterIntention(e.target.value || null)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-cannabis-500"
          >
            <option value="">All Reviews</option>
            <optgroup label="Medical">
              <option value="pain">Pain Relief</option>
              <option value="insomnia">Sleep/Insomnia</option>
              <option value="anxiety">Anxiety</option>
              <option value="nausea">Nausea</option>
              <option value="spasms">Spasms</option>
            </optgroup>
            <optgroup label="Mood/Wellness">
              <option value="socializing">Socializing</option>
              <option value="creativity">Creativity</option>
              <option value="deep_relaxation">Deep Relaxation</option>
              <option value="focus">Focus</option>
              <option value="post_workout">Post-Workout</option>
            </optgroup>
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-sm font-semibold mb-2 text-gray-700">Sort By</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-cannabis-500"
          >
            <option value="recent">Most Recent</option>
            <option value="helpful">Most Helpful</option>
            <option value="rating_high">Highest Rated</option>
          </select>
        </div>
      </div>

      {/* Reviews List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="border rounded-lg p-4 animate-pulse">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
                  <div className="h-3 bg-gray-100 rounded w-24"></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-3 bg-gray-200 rounded w-full"></div>
                <div className="h-3 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          ))}
        </div>
      ) : reviews.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <p className="mt-4 text-gray-600 font-medium">No reviews yet</p>
          <p className="text-gray-500">Be the first to share your experience with this product!</p>
          {!showForm && (
            <button
              onClick={() => setShowForm(true)}
              className="mt-4 px-4 py-2 bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700 transition-colors"
            >
              Write the First Review
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} onUpvote={loadReviews} />
          ))}
        </div>
      )}
    </div>
  )
}

interface ReviewCardProps {
  review: Review
  onUpvote: () => void
}

function ReviewCard({ review, onUpvote }: ReviewCardProps) {
  const [upvoting, setUpvoting] = useState(false)

  const handleUpvote = async () => {
    try {
      setUpvoting(true)
      await api.post(`/api/reviews/${review.id}/upvote`)
      onUpvote()
    } catch (error) {
      console.error('Failed to upvote:', error)
    } finally {
      setUpvoting(false)
    }
  }

  const getIntentionIcon = (type: string | null) => {
    if (type === 'medical') return '🏥'
    if (type === 'mood') return '😊'
    return '📝'
  }

  const getIntentionLabel = (tag: string | null) => {
    if (!tag) return ''
    return tag.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cannabis-100 rounded-full flex items-center justify-center text-cannabis-700 font-bold">
            {review.username.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="font-semibold text-gray-900">{review.username}</p>
            <p className="text-sm text-gray-500">{formatDate(review.created_at)}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {[...Array(5)].map((_, i) => (
            <svg
              key={i}
              className={`w-5 h-5 ${i < review.rating ? 'text-yellow-400' : 'text-gray-300'}`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          ))}
          <span className="ml-1 text-sm font-semibold text-gray-700">{review.rating}/5</span>
        </div>
      </div>

      {/* Rating Breakdown */}
      <div className="flex gap-4 mb-3 text-sm">
        {review.effects_rating && (
          <div className="flex items-center gap-1">
            <span className="text-gray-600">Effects:</span>
            <span className="font-semibold text-cannabis-700">{review.effects_rating}★</span>
          </div>
        )}
        {review.taste_rating && (
          <div className="flex items-center gap-1">
            <span className="text-gray-600">Taste:</span>
            <span className="font-semibold text-cannabis-700">{review.taste_rating}★</span>
          </div>
        )}
        {review.value_rating && (
          <div className="flex items-center gap-1">
            <span className="text-gray-600">Value:</span>
            <span className="font-semibold text-cannabis-700">{review.value_rating}★</span>
          </div>
        )}
      </div>

      {/* Intention Tag */}
      {review.intention_tag && (
        <div className="mb-3">
          <span className="inline-flex items-center gap-1 px-3 py-1 bg-cannabis-100 text-cannabis-800 rounded-full text-sm font-medium">
            <span>{getIntentionIcon(review.intention_type)}</span>
            <span>{getIntentionLabel(review.intention_tag)}</span>
          </span>
        </div>
      )}

      {/* Comment */}
      {review.comment && (
        <p className="text-gray-700 mb-4 leading-relaxed">{review.comment}</p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-sm border-t pt-3">
        <button
          onClick={handleUpvote}
          disabled={upvoting}
          className="flex items-center gap-2 text-cannabis-600 hover:text-cannabis-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
          </svg>
          <span>{upvoting ? 'Upvoting...' : `Helpful (${review.upvotes})`}</span>
        </button>
      </div>
    </div>
  )
}
