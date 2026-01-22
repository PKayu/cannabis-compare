'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import { api } from '@/lib/api'
import Link from 'next/link'

interface UserProfile {
  id: string
  email: string
  username: string
  created_at: string
  review_count: number
}

interface Review {
  id: string
  product_id: string
  product_name: string
  rating: number
  effects_rating: number
  taste_rating: number
  value_rating: number
  comment: string
  upvotes: number
  created_at: string
}

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const supabase = createClientComponentClient()
  const router = useRouter()

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      setLoading(true)
      setError(null)

      // Check if user is authenticated
      const { data, error: sessionError } = await supabase.auth.getSession()
      if (sessionError || !data.session) {
        router.push('/auth/login')
        return
      }

      // Get user profile from backend
      const userRes = await api.get('/api/users/me')
      setUser(userRes.data)

      // Get user's reviews
      const reviewsRes = await api.get('/api/users/me/reviews')
      setReviews(reviewsRes.data || [])
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to load profile'
      setError(message)
      // If unauthorized, redirect to login
      if (err.response?.status === 401) {
        setTimeout(() => router.push('/auth/login'), 2000)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push('/')
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cannabis-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading your profile...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-700 mb-2">Error Loading Profile</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <div className="flex gap-3">
              <button
                onClick={loadProfile}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => router.push('/')}
                className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors"
              >
                Back to Home
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">No User Data</h1>
          <p className="text-gray-600 mb-6">Unable to load user information. Please try signing in again.</p>
          <button
            onClick={() => router.push('/auth/login')}
            className="px-6 py-2 bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700 transition-colors"
          >
            Sign In
          </button>
        </div>
      </div>
    )
  }

  const memberSince = new Date(user.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold text-cannabis-700">My Profile</h1>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Sign Out
            </button>
          </div>
          <p className="text-gray-600">Manage your account and review history</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Profile Card */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Account Information</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-500 uppercase mb-1">Email</p>
              <p className="text-lg text-gray-900">{user.email}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-500 uppercase mb-1">Username</p>
              <p className="text-lg text-gray-900">{user.username}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-500 uppercase mb-1">Member Since</p>
              <p className="text-lg text-gray-900">{memberSince}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-500 uppercase mb-1">Reviews Posted</p>
              <p className="text-lg text-gray-900">{user.review_count}</p>
            </div>
          </div>
        </div>

        {/* Reviews Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">My Reviews</h2>
            {user.review_count > 0 && (
              <span className="text-sm text-gray-500">{user.review_count} total</span>
            )}
          </div>

          {reviews.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">You haven't posted any reviews yet.</p>
              <Link
                href="/products/search"
                className="inline-block px-6 py-2 bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700 transition-colors"
              >
                Browse Products
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {reviews.map((review) => (
                <div
                  key={review.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  {/* Review Header */}
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <Link
                        href={`/products/${review.product_id}`}
                        className="text-lg font-semibold text-cannabis-600 hover:text-cannabis-700"
                      >
                        {review.product_name}
                      </Link>
                      <p className="text-sm text-gray-500">
                        {new Date(review.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold text-cannabis-600">
                          {review.rating}
                        </span>
                        <span className="text-sm text-gray-500">/5</span>
                      </div>
                    </div>
                  </div>

                  {/* Ratings Summary */}
                  <div className="grid grid-cols-3 gap-3 mb-4 py-3 border-y border-gray-200">
                    <div className="text-center">
                      <p className="text-xs text-gray-500 uppercase mb-1">Effects</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {review.effects_rating}/5
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500 uppercase mb-1">Taste</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {review.taste_rating}/5
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500 uppercase mb-1">Value</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {review.value_rating}/5
                      </p>
                    </div>
                  </div>

                  {/* Review Comment */}
                  {review.comment && (
                    <p className="text-gray-700 mb-3">{review.comment}</p>
                  )}

                  {/* Review Footer */}
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-500">
                      {review.upvotes === 1 ? '1 upvote' : `${review.upvotes} upvotes`}
                    </span>
                    <Link
                      href={`/products/${review.product_id}`}
                      className="text-cannabis-600 hover:text-cannabis-700 font-medium"
                    >
                      View Product →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Coming Soon Features */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-3">Coming Soon</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>✓ Product Watchlist</li>
            <li>✓ Price Drop Alerts</li>
            <li>✓ Stock Availability Notifications</li>
            <li>✓ Profile Preferences</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
