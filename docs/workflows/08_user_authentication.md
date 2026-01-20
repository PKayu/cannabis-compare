---
description: Implement Supabase Auth with magic links, age gate verification, user profiles, and session management.
auto_execution_mode: 1
---

## Context

This workflow implements user authentication as defined in PRD section 6.1:
- Supabase Auth with magic links and OAuth
- Age gate (21+ verification)
- User profiles and history
- Session management
- JWT token handling

## Steps

### 1. Configure Supabase Auth

Set up Supabase project at https://supabase.com:
1. Create new project
2. Go to Authentication settings
3. Enable email/password and OAuth providers (Google)
4. Set redirect URLs: `http://localhost:3000/auth/callback`

Get credentials and add to `frontend/.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 2. Implement Age Gate Component

Create `frontend/components/AgeGate.tsx`:

```typescript
'use client'

import React, { useState } from 'react'

interface AgeGateProps {
  onVerify: () => void
}

export default function AgeGate({ onVerify }: AgeGateProps) {
  const [accepted, setAccepted] = useState(false)
  const [birthDate, setBirthDate] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const birth = new Date(birthDate)
    const today = new Date()
    let age = today.getFullYear() - birth.getFullYear()
    const monthDiff = today.getMonth() - birth.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--
    }

    if (age >= 21) {
      localStorage.setItem('age_verified', 'true')
      onVerify()
    } else {
      alert('You must be 21 or older to access this site.')
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-8 max-w-md">
        <h2 className="text-2xl font-bold mb-4">Age Verification</h2>
        <p className="text-gray-600 mb-6">
          This site is only for individuals 21 years of age or older.
        </p>

        <form onSubmit={handleSubmit}>
          <input
            type="date"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            className="w-full px-3 py-2 border rounded mb-4"
            required
          />

          <label className="flex items-center mb-6">
            <input
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm">
              I confirm I am 21 years or older and have a valid medical cannabis card.
            </span>
          </label>

          <button
            type="submit"
            disabled={!accepted || !birthDate}
            className="w-full px-4 py-2 bg-cannabis-600 text-white rounded disabled:opacity-50"
          >
            Continue
          </button>
        </form>

        <p className="text-xs text-gray-500 text-center mt-4">
          For informational purposes only. Not affiliated with any dispensary.
        </p>
      </div>
    </div>
  )
}
```

### 3. Create Magic Link Login Flow

Create `frontend/app/auth/login/page.tsx`:

```typescript
'use client'

import React, { useState } from 'react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const supabase = createClientComponentClient()
  const router = useRouter()

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`
        }
      })

      if (error) throw error
      setMessage('Check your email for the login link!')
    } catch (error) {
      setMessage(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow">
        <h1 className="text-3xl font-bold mb-6 text-cannabis-700">Sign In</h1>

        <form onSubmit={handleMagicLink}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-3 py-2 border rounded mb-4"
            required
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-cannabis-600 text-white rounded hover:bg-cannabis-700 disabled:opacity-50"
          >
            {loading ? 'Sending...' : 'Send Magic Link'}
          </button>
        </form>

        {message && <p className="mt-4 text-center text-sm">{message}</p>}

        <div className="mt-6 pt-6 border-t">
          <button
            onClick={async () => {
              const { error } = await supabase.auth.signInWithOAuth({
                provider: 'google',
                options: {
                  redirectTo: `${window.location.origin}/auth/callback`
                }
              })
            }}
            className="w-full px-4 py-2 bg-white border-2 border-gray-300 text-gray-700 rounded hover:bg-gray-50"
          >
            Sign in with Google
          </button>
        </div>
      </div>
    </div>
  )
}
```

### 4. Add OAuth Providers

(Done in step 3 - Google OAuth implemented)

### 5. Create User Profile API Endpoints

Create `backend/routers/users.py`:

```python
"""User profile endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Review

router = APIRouter(prefix="/api/users", tags=["users"])

def get_current_user(token: str = Depends(...)) -> str:
    """Extract user ID from JWT token"""
    # TODO: Implement JWT verification
    return token

@router.get("/me")
async def get_profile(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    review_count = db.query(Review).filter(Review.user_id == user_id).count()

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "created_at": user.created_at,
        "review_count": review_count
    }

@router.get("/me/reviews")
async def get_user_reviews(
    user_id: str = Depends(get_current_user),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get user's review history"""

    reviews = (
        db.query(Review)
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .all()
    )

    return reviews
```

### 6. Build Profile Page Component

Create `frontend/app/profile/page.tsx`:

```typescript
'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import { api } from '@/lib/api'

export default function ProfilePage() {
  const [user, setUser] = useState(null)
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const supabase = createClientComponentClient()
  const router = useRouter()

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      const { data } = await supabase.auth.getSession()
      if (!data.session) {
        router.push('/auth/login')
        return
      }

      const userRes = await api.get('/api/users/me')
      const reviewsRes = await api.get('/api/users/me/reviews')

      setUser(userRes.data)
      setReviews(reviewsRes.data)
    } catch (error) {
      console.error('Failed to load profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/')
  }

  if (loading) return <div>Loading...</div>
  if (!user) return <div>Not logged in</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-8">
          <h1 className="text-3xl font-bold text-cannabis-700 mb-6">My Profile</h1>

          <div className="grid grid-cols-2 gap-6 mb-8">
            <div>
              <p className="text-gray-600">Email</p>
              <p className="text-lg font-semibold">{user.email}</p>
            </div>
            <div>
              <p className="text-gray-600">Username</p>
              <p className="text-lg font-semibold">{user.username}</p>
            </div>
            <div>
              <p className="text-gray-600">Member Since</p>
              <p className="text-lg font-semibold">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Reviews Posted</p>
              <p className="text-lg font-semibold">{user.review_count}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Sign Out
          </button>
        </div>

        {/* Review History */}
        <div className="mt-8 bg-white rounded-lg shadow p-8">
          <h2 className="text-2xl font-bold mb-6">My Reviews</h2>
          {reviews.length === 0 ? (
            <p className="text-gray-600">You haven't posted any reviews yet.</p>
          ) : (
            <div className="space-y-4">
              {reviews.map((review) => (
                <div key={review.id} className="border rounded p-4">
                  <p className="font-bold">{review.product.name}</p>
                  <p className="text-gray-600">{review.comment}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(review.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
```

### 7. Implement Session Management

Update `frontend/lib/api.ts` to include auth tokens:

```typescript
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

const supabase = createClientComponentClient()

apiClient.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  if (data?.session?.access_token) {
    config.headers.Authorization = `Bearer ${data.session.access_token}`
  }
  return config
})
```

### 8. Add Authentication Guards to Routes

Create `frontend/components/ProtectedRoute.tsx`:

```typescript
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [isAuthed, setIsAuthed] = useState(false)
  const supabase = createClientComponentClient()
  const router = useRouter()

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        setIsAuthed(true)
      } else {
        router.push('/auth/login')
      }
    })
  }, [])

  return isAuthed ? <>{children}</> : <div>Redirecting...</div>
}
```

### 9. Update API Client with Auth Tokens

(Done in step 7)

### 10. Test Authentication Flow End-to-End

Test scenarios:
1. Sign up with magic link
2. Receive email and click link
3. Redirect to profile page
4. Sign out
5. Sign in again with different method (OAuth)
6. Access protected routes

## Success Criteria

- [ ] Supabase Auth configured with magic links
- [ ] Age gate component displays correctly
- [ ] Age verification working (21+ check)
- [ ] Magic link login functional
- [ ] OAuth (Google) login working
- [ ] User profile page loads after login
- [ ] Review history displays correctly
- [ ] Session tokens in API requests
- [ ] Protected routes redirect to login
- [ ] Sign out clears session
- [ ] Authentication persists across page reloads
- [ ] No TypeScript errors
