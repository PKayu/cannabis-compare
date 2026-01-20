---
description: Build dual-track intention tag system (Medical + Mood/Wellness), implement 1-5 star ratings, add batch tracking, and create review submission forms.
auto_execution_mode: 1
---

## Context

This workflow implements the community review system as defined in PRD section 4.3:
- Dual-track intention tags (Medical + Mood/Wellness)
- Standardized 1-5 star ratings (Effects, Taste, Value)
- Optional batch/cultivation date tracking
- Review submission and display
- Filtering by intention

## Steps

### 1. Review PRD Review System Requirements

Read PRD section 4.3:
- Medical intentions: Pain, Insomnia, Anxiety, Nausea, Spasms
- Mood/Wellness: Socializing, Creativity, Deep Relaxation, Focus, Post-Workout
- Star ratings: Effects, Taste, Value (1-5)
- Batch tracking: Optional batch number or cultivation date

### 2. Create Intention Tag Enums

Create `backend/models/enums.py`:

```python
"""Enum definitions for review system"""
from enum import Enum

class MedicalIntention(str, Enum):
    PAIN = "pain"
    INSOMNIA = "insomnia"
    ANXIETY = "anxiety"
    NAUSEA = "nausea"
    SPASMS = "spasms"

class MoodIntention(str, Enum):
    SOCIALIZING = "socializing"
    CREATIVITY = "creativity"
    DEEP_RELAXATION = "deep_relaxation"
    FOCUS = "focus"
    POST_WORKOUT = "post_workout"

# Combined for queries
ALL_INTENTIONS = {
    "medical": [i.value for i in MedicalIntention],
    "mood": [i.value for i in MoodIntention]
}
```

### 3. Update Review Model with Intention Tags

Update `backend/models.py`:

```python
class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Star ratings
    effects_rating = Column(Integer, nullable=False)  # 1-5
    taste_rating = Column(Integer, nullable=False)    # 1-5
    value_rating = Column(Integer, nullable=False)    # 1-5
    overall_rating = Column(Integer, nullable=False)  # 1-5, computed from above

    # Intention tags (can have multiple)
    intention_type = Column(String)  # "medical" or "mood"
    intention_tag = Column(String)   # e.g., "pain", "socializing"

    # Batch tracking
    batch_number = Column(String, nullable=True)
    cultivation_date = Column(DateTime, nullable=True)

    # Written review
    comment = Column(Text, nullable=True)

    # Community engagement
    upvotes = Column(Integer, default=0)

    # Foreign keys
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")
```

### 4. Create Review Submission API Endpoint

Create `backend/routers/reviews.py`:

```python
"""Review endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Review, Product
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

class ReviewCreate(BaseModel):
    product_id: str
    effects_rating: int  # 1-5
    taste_rating: int    # 1-5
    value_rating: int    # 1-5
    intention_type: str  # "medical" or "mood"
    intention_tag: str   # specific tag
    batch_number: str | None = None
    cultivation_date: str | None = None
    comment: str | None = None

@router.post("/")
async def create_review(
    review_data: ReviewCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a new review"""

    # Validate ratings
    for rating in [review_data.effects_rating, review_data.taste_rating, review_data.value_rating]:
        if not 1 <= rating <= 5:
            raise HTTPException(status_code=400, detail="Ratings must be 1-5")

    # Validate product exists
    product = db.query(Product).filter(Product.id == review_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Create review
    overall = (
        review_data.effects_rating +
        review_data.taste_rating +
        review_data.value_rating
    ) // 3

    review = Review(
        user_id=user_id,
        product_id=review_data.product_id,
        effects_rating=review_data.effects_rating,
        taste_rating=review_data.taste_rating,
        value_rating=review_data.value_rating,
        overall_rating=overall,
        intention_type=review_data.intention_type,
        intention_tag=review_data.intention_tag,
        batch_number=review_data.batch_number,
        cultivation_date=review_data.cultivation_date,
        comment=review_data.comment
    )

    db.add(review)
    db.commit()

    return {
        "id": review.id,
        "status": "created"
    }

@router.get("/{product_id}")
async def get_reviews(
    product_id: str,
    intention_type: str | None = None,
    intention_tag: str | None = None,
    sort_by: str = "recent",
    db: Session = Depends(get_db)
):
    """Get reviews for a product with optional filtering"""

    query = db.query(Review).filter(Review.product_id == product_id)

    if intention_type:
        query = query.filter(Review.intention_type == intention_type)

    if intention_tag:
        query = query.filter(Review.intention_tag == intention_tag)

    if sort_by == "recent":
        query = query.order_by(Review.created_at.desc())
    elif sort_by == "helpful":
        query = query.order_by(Review.upvotes.desc())
    elif sort_by == "rating_high":
        query = query.order_by(Review.overall_rating.desc())

    reviews = query.all()

    return [
        {
            "id": r.id,
            "user": r.user.username,
            "effects_rating": r.effects_rating,
            "taste_rating": r.taste_rating,
            "value_rating": r.value_rating,
            "overall_rating": r.overall_rating,
            "intention_type": r.intention_type,
            "intention_tag": r.intention_tag,
            "batch_number": r.batch_number,
            "comment": r.comment,
            "upvotes": r.upvotes,
            "created_at": r.created_at
        }
        for r in reviews
    ]
```

### 5. Build Review Listing API with Filtering

(Done in step 4 - filtering by intention_type and intention_tag)

### 6. Create Review Form Component

Create `frontend/components/ReviewForm.tsx`:

```typescript
'use client'

import React, { useState } from 'react'
import { api } from '@/lib/api'

interface ReviewFormProps {
  productId: string
  onSubmit?: () => void
}

export default function ReviewForm({ productId, onSubmit }: ReviewFormProps) {
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

  const medicalIntentions = ['pain', 'insomnia', 'anxiety', 'nausea', 'spasms']
  const moodIntentions = ['socializing', 'creativity', 'deep_relaxation', 'focus', 'post_workout']

  const intentionOptions = formData.intention_type === 'medical' ? medicalIntentions : moodIntentions

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      await api.post('/api/reviews', {
        product_id: productId,
        ...formData
      })

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
    } catch (error) {
      console.error('Failed to submit review:', error)
    }
  }

  const RatingInput = ({ label, value, onChange }) => (
    <div className="mb-4">
      <label className="block font-semibold mb-2">{label}</label>
      <div className="flex gap-2">
        {[1, 2, 3, 4, 5].map((rating) => (
          <button
            key={rating}
            onClick={() => onChange(rating)}
            className={`w-10 h-10 rounded border-2 ${
              value === rating ? 'border-cannabis-600 bg-cannabis-100' : 'border-gray-300'
            }`}
          >
            {rating}★
          </button>
        ))}
      </div>
    </div>
  )

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-2xl font-bold mb-6">Share Your Review</h3>

      {/* Ratings */}
      <div className="mb-8">
        <p className="font-bold mb-4">How would you rate this product?</p>
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

      {/* Intention Tags */}
      <div className="mb-8 p-4 bg-cannabis-50 rounded">
        <p className="font-bold mb-4">Why did you use this product?</p>

        <div className="mb-4">
          <label className="block font-semibold mb-2">Use Type</label>
          <select
            value={formData.intention_type}
            onChange={(e) => setFormData({
              ...formData,
              intention_type: e.target.value,
              intention_tag: e.target.value === 'medical' ? 'pain' : 'socializing'
            })}
            className="w-full px-3 py-2 border rounded"
          >
            <option value="medical">Medical</option>
            <option value="mood">Mood/Wellness</option>
          </select>
        </div>

        <div>
          <label className="block font-semibold mb-2">Specific Use</label>
          <select
            value={formData.intention_tag}
            onChange={(e) => setFormData({ ...formData, intention_tag: e.target.value })}
            className="w-full px-3 py-2 border rounded"
          >
            {intentionOptions.map((option) => (
              <option key={option} value={option}>
                {option.replace('_', ' ').toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Batch Tracking */}
      <div className="mb-8">
        <p className="font-bold mb-4">Product Details (Optional)</p>
        <input
          type="text"
          placeholder="Batch number"
          value={formData.batch_number}
          onChange={(e) => setFormData({ ...formData, batch_number: e.target.value })}
          className="w-full px-3 py-2 border rounded mb-2"
        />
        <input
          type="date"
          placeholder="Cultivation date"
          value={formData.cultivation_date}
          onChange={(e) => setFormData({ ...formData, cultivation_date: e.target.value })}
          className="w-full px-3 py-2 border rounded"
        />
      </div>

      {/* Comment */}
      <div className="mb-6">
        <label className="block font-semibold mb-2">Your Thoughts</label>
        <textarea
          value={formData.comment}
          onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
          placeholder="Share your experience..."
          className="w-full px-3 py-2 border rounded"
          rows={4}
        />
      </div>

      <button
        type="submit"
        className="w-full px-4 py-2 bg-cannabis-600 text-white rounded hover:bg-cannabis-700"
      >
        Submit Review
      </button>
    </form>
  )
}
```

### 7. Implement Dual-Track Tag Selection UI

(Done in step 6 - selection between Medical and Mood/Wellness)

### 8. Add 1-5 Star Rating Inputs

(Done in step 6 - Effects, Taste, Value ratings)

### 9. Add Batch Tracking Field

(Done in step 6 - batch_number and cultivation_date)

### 10. Build Review Display Component

Create `frontend/components/ReviewsSection.tsx`:

```typescript
import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'

interface ReviewsSectionProps {
  productId: string
}

export default function ReviewsSection({ productId }: ReviewsSectionProps) {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterIntention, setFilterIntention] = useState(null)
  const [sortBy, setSortBy] = useState('recent')

  useEffect(() => {
    loadReviews()
  }, [filterIntention, sortBy])

  const loadReviews = async () => {
    try {
      const res = await api.get(`/api/reviews/${productId}`, {
        params: {
          intention_tag: filterIntention,
          sort_by: sortBy
        }
      })
      setReviews(res.data)
    } catch (error) {
      console.error('Failed to load reviews:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6 flex gap-4">
        <div>
          <label className="block font-semibold mb-2">Filter by Intention</label>
          <select
            value={filterIntention || ''}
            onChange={(e) => setFilterIntention(e.target.value || null)}
            className="px-3 py-2 border rounded"
          >
            <option value="">All Reviews</option>
            <option value="pain">Pain Relief</option>
            <option value="insomnia">Sleep/Insomnia</option>
            <option value="socializing">Socializing</option>
            <option value="focus">Focus</option>
          </select>
        </div>

        <div>
          <label className="block font-semibold mb-2">Sort By</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 border rounded"
          >
            <option value="recent">Recent</option>
            <option value="helpful">Most Helpful</option>
            <option value="rating_high">Highest Rated</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div>Loading reviews...</div>
      ) : reviews.length === 0 ? (
        <div className="text-gray-600">No reviews yet. Be the first to review!</div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} />
          ))}
        </div>
      )}
    </div>
  )
}

function ReviewCard({ review }) {
  const handleUpvote = async () => {
    try {
      await api.post(`/api/reviews/${review.id}/upvote`)
    } catch (error) {
      console.error('Failed to upvote:', error)
    }
  }

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="flex justify-between mb-2">
        <p className="font-bold">{review.user}</p>
        <p className="text-sm text-gray-500">{new Date(review.created_at).toLocaleDateString()}</p>
      </div>

      <div className="flex gap-4 mb-3">
        <div>
          <p className="text-sm text-gray-600">Effects: {review.effects_rating}★</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Taste: {review.taste_rating}★</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Value: {review.value_rating}★</p>
        </div>
      </div>

      <p className="text-sm text-cannabis-600 mb-2">
        {review.intention_type === 'medical' ? '🏥' : '😊'} {review.intention_tag}
      </p>

      {review.comment && <p className="text-gray-700 mb-3">{review.comment}</p>}

      <div className="flex justify-between items-center text-sm">
        <button
          onClick={handleUpvote}
          className="text-cannabis-600 hover:underline"
        >
          👍 {review.upvotes} Helpful
        </button>
      </div>
    </div>
  )
}
```

### 11. Implement Review Filtering by Intention

(Done in step 10 - filtering in ReviewsSection)

### 12. Add Review Upvoting

Create `backend/routers/reviews.py` endpoint:

```python
@router.post("/{review_id}/upvote")
async def upvote_review(
    review_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upvote a review"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.upvotes += 1
    db.commit()

    return {"upvotes": review.upvotes}
```

### 13. Test Review Workflow End-to-End

Test scenarios:
1. Submit review with medical intention
2. Submit review with mood intention
3. Filter reviews by intention
4. Sort by recent/helpful
5. Upvote a review
6. View batch tracking information

## Success Criteria

- [ ] Intention tag enums created
- [ ] Review model updated with all fields
- [ ] Review submission endpoint working
- [ ] Review filtering by intention functional
- [ ] Dual-track UI displays correctly
- [ ] Star rating inputs functional (1-5)
- [ ] Batch tracking fields optional but captured
- [ ] Review form submits successfully
- [ ] Review display component shows all information
- [ ] Filtering by intention tag working
- [ ] Sorting by recent/helpful/rating working
- [ ] Upvoting reviews functional
- [ ] 3+ reviews per top SKU within 6 months (goal)
- [ ] No TypeScript errors
