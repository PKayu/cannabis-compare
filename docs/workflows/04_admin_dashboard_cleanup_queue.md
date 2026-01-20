---
description: Build admin dashboard with Cleanup Queue UI for product normalization, merge/split actions, and outlier price detection alerts.
auto_execution_mode: 1
---

## Context

This workflow implements the Admin Dashboard as defined in PRD section 4.4:
- Cleanup Queue UI for resolving product naming discrepancies
- One-click merge/split functionality
- Outlier price detection for data quality
- Manual override interface for flagged products

## Steps

### 1. Read PRD Admin Requirements

Read PRD section 4.4 (Admin Dashboard):
- Cleanup Queue for flagged products
- Merge/split actions
- Outlier alerts for price anomalies
- Admin authentication requirements

### 2. Create Backend API Routes for ScraperFlags CRUD

Create `backend/routers/admin_flags.py`:

```python
"""Admin routes for ScraperFlag management"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import ScraperFlag
from datetime import datetime

router = APIRouter(prefix="/api/admin/flags", tags=["admin"])

@router.get("/pending", response_model=List[dict])
async def get_pending_flags(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """Get pending ScraperFlags for admin review"""
    flags = (
        db.query(ScraperFlag)
        .filter(ScraperFlag.status == "pending")
        .order_by(ScraperFlag.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return flags

@router.post("/approve/{flag_id}")
async def approve_flag(
    flag_id: str,
    notes: str = "",
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Approve merging flagged product to matched product"""
    flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    flag.status = "approved"
    flag.resolved_by = admin_id
    flag.resolved_at = datetime.utcnow()
    flag.admin_notes = notes

    db.commit()
    return {"status": "approved", "product_id": flag.matched_product_id}

@router.post("/reject/{flag_id}")
async def reject_flag(
    flag_id: str,
    notes: str = "",
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Reject flag and create new product"""
    flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    flag.status = "rejected"
    flag.resolved_by = admin_id
    flag.resolved_at = datetime.utcnow()
    flag.admin_notes = notes

    db.commit()
    return {"status": "rejected"}

@router.get("/stats")
async def get_flag_stats(db: Session = Depends(get_db)):
    """Get statistics on ScraperFlags"""
    pending = db.query(ScraperFlag).filter(ScraperFlag.status == "pending").count()
    approved = db.query(ScraperFlag).filter(ScraperFlag.status == "approved").count()
    rejected = db.query(ScraperFlag).filter(ScraperFlag.status == "rejected").count()

    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "total": pending + approved + rejected
    }
```

### 3. Build Merge/Split Product Endpoints

Add to `backend/routers/admin_flags.py`:

```python
@router.post("/merge")
async def merge_products(
    source_product_id: str,
    target_product_id: str,
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Merge source product into target product"""
    from backend.models import Product, Price

    source = db.query(Product).filter(Product.id == source_product_id).first()
    target = db.query(Product).filter(Product.id == target_product_id).first()

    if not source or not target:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update all prices from source to target
    db.query(Price).filter(Price.product_id == source_product_id).update(
        {Price.product_id: target_product_id}
    )

    # Mark source as duplicate
    source.is_master = False
    source.master_product_id = target_product_id

    db.commit()
    return {"status": "merged", "target_id": target_product_id}

@router.post("/split")
async def split_product(
    product_id: str,
    product_name: str,
    brand_id: str,
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Split a product into its own entry"""
    from backend.models import Product, Price

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Create new master product
    new_product = Product(
        name=product_name,
        product_type=product.product_type,
        brand_id=brand_id,
        thc_percentage=product.thc_percentage,
        cbd_percentage=product.cbd_percentage,
        is_master=True
    )
    db.add(new_product)
    db.commit()

    return {"status": "split", "new_product_id": new_product.id}
```

### 4. Implement Outlier Detection Algorithm

Create `backend/services/quality/outlier_detection.py`:

```python
"""Detect price outliers for data quality"""
import statistics
from typing import List, Dict
from backend.models import Price

class OutlierDetector:
    """Detects price anomalies"""

    STDDEV_THRESHOLD = 2.0  # 2 standard deviations = outlier

    @staticmethod
    def detect_price_outliers(prices: List[Price]) -> List[Dict]:
        """Find prices significantly different from state average"""
        if len(prices) < 3:
            return []  # Need at least 3 data points

        price_amounts = [p.amount for p in prices]
        mean = statistics.mean(price_amounts)
        stdev = statistics.stdev(price_amounts)

        outliers = []
        for price in prices:
            z_score = abs((price.amount - mean) / stdev) if stdev > 0 else 0

            if z_score > OutlierDetector.STDDEV_THRESHOLD:
                outliers.append({
                    "price_id": price.id,
                    "dispensary_id": price.dispensary_id,
                    "amount": price.amount,
                    "state_average": mean,
                    "deviation_percent": ((price.amount - mean) / mean) * 100,
                    "z_score": z_score,
                    "severity": "high" if z_score > 3 else "medium"
                })

        return sorted(outliers, key=lambda x: x["z_score"], reverse=True)

    @staticmethod
    def get_product_price_range(db, product_id: str) -> Dict:
        """Get min/max/avg prices for a product across dispensaries"""
        prices = db.query(Price).filter(Price.product_id == product_id).all()

        if not prices:
            return {}

        amounts = [p.amount for p in prices]
        return {
            "min": min(amounts),
            "max": max(amounts),
            "avg": statistics.mean(amounts),
            "count": len(amounts),
            "range": max(amounts) - min(amounts)
        }
```

### 5. Create Frontend Admin Page Route

Create `frontend/app/(admin)/admin/cleanup/page.tsx`:

```typescript
'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'

interface ScraperFlag {
  id: string
  original_name: string
  brand_name: string
  dispensary_id: string
  matched_product_id: string | null
  confidence_score: number
  created_at: string
}

export default function CleanupQueuePage() {
  const [flags, setFlags] = useState<ScraperFlag[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    loadFlags()
    loadStats()
  }, [])

  const loadFlags = async () => {
    try {
      const res = await api.get('/api/admin/flags/pending?limit=50')
      setFlags(res.data)
    } catch (error) {
      console.error('Failed to load flags:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await api.get('/api/admin/flags/stats')
      setStats(res.data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const handleApprove = async (flagId: string, notes: string) => {
    try {
      await api.post(`/api/admin/flags/approve/${flagId}`, { notes })
      setFlags(flags.filter(f => f.id !== flagId))
    } catch (error) {
      console.error('Failed to approve flag:', error)
    }
  }

  const handleReject = async (flagId: string, notes: string) => {
    try {
      await api.post(`/api/admin/flags/reject/${flagId}`, { notes })
      setFlags(flags.filter(f => f.id !== flagId))
    } catch (error) {
      console.error('Failed to reject flag:', error)
    }
  }

  if (loading) return <div>Loading...</div>

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Cleanup Queue</h1>

      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-yellow-50 p-4 rounded border border-yellow-200">
            <p className="text-sm text-yellow-700">Pending</p>
            <p className="text-2xl font-bold text-yellow-900">{stats.pending}</p>
          </div>
          <div className="bg-green-50 p-4 rounded border border-green-200">
            <p className="text-sm text-green-700">Approved</p>
            <p className="text-2xl font-bold text-green-900">{stats.approved}</p>
          </div>
          <div className="bg-red-50 p-4 rounded border border-red-200">
            <p className="text-sm text-red-700">Rejected</p>
            <p className="text-2xl font-bold text-red-900">{stats.rejected}</p>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {flags.map((flag) => (
          <FlagCard
            key={flag.id}
            flag={flag}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        ))}
      </div>
    </div>
  )
}

function FlagCard({ flag, onApprove, onReject }) {
  const [notes, setNotes] = useState('')
  const [processing, setProcessing] = useState(false)

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="mb-4">
        <h3 className="font-bold text-lg">{flag.original_name}</h3>
        <p className="text-gray-600">{flag.brand_name}</p>
        <p className="text-sm text-gray-500">
          Confidence: {(flag.confidence_score * 100).toFixed(1)}%
        </p>
      </div>

      <textarea
        className="w-full p-2 border rounded mb-4"
        placeholder="Admin notes..."
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />

      <div className="flex gap-2">
        <button
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          onClick={() => {
            setProcessing(true)
            onApprove(flag.id, notes).finally(() => setProcessing(false))
          }}
          disabled={processing}
        >
          Approve
        </button>
        <button
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
          onClick={() => {
            setProcessing(true)
            onReject(flag.id, notes).finally(() => setProcessing(false))
          }}
          disabled={processing}
        >
          Reject
        </button>
      </div>
    </div>
  )
}
```

### 6. Build Cleanup Queue UI Component

Create `frontend/components/CleanupQueueTable.tsx` for a table view of multiple flags (reusable component).

### 7. Implement Merge Action with Preview

Add merge preview in `frontend/components/MergePreview.tsx`:

```typescript
interface MergePreviewProps {
  sourceProduct: Product
  targetProduct: Product
  onMerge: () => Promise<void>
}

export function MergePreview({ sourceProduct, targetProduct, onMerge }: MergePreviewProps) {
  return (
    <div className="border rounded p-4">
      <h3 className="font-bold mb-4">Merge Preview</h3>
      <p>Merging products:</p>
      <p className="text-red-600">{sourceProduct.name} → {targetProduct.name}</p>
      <p className="text-sm text-gray-600 mt-2">All prices will be linked to the target product</p>
      <button
        onClick={onMerge}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
      >
        Confirm Merge
      </button>
    </div>
  )
}
```

### 8. Implement Split Action

Add split functionality in backend and frontend.

### 9. Add Outlier Alert Badges

Create `frontend/components/OutlierAlert.tsx`:

```typescript
interface OutlierAlertProps {
  outlier: {
    deviation_percent: number
    severity: 'low' | 'medium' | 'high'
  }
}

export function OutlierAlert({ outlier }: OutlierAlertProps) {
  const bgColor = {
    low: 'bg-yellow-50',
    medium: 'bg-orange-50',
    high: 'bg-red-50'
  }[outlier.severity]

  const borderColor = {
    low: 'border-yellow-200',
    medium: 'border-orange-200',
    high: 'border-red-200'
  }[outlier.severity]

  return (
    <div className={`${bgColor} ${borderColor} border rounded p-3`}>
      <p className="font-semibold">⚠️ Price Outlier</p>
      <p className="text-sm">{outlier.deviation_percent.toFixed(1)}% from state average</p>
    </div>
  )
}
```

### 10. Test Admin Workflow End-to-End

Create test scenarios:
1. Approve a flagged product merge
2. Reject a flagged product
3. Manually merge two products
4. Split a product
5. View outlier alerts

### 11. Add Authentication Guard for Admin Routes

Add to `backend/routers/admin_flags.py`:

```python
from fastapi import Depends, HTTPException
from backend.models import User

async def verify_admin(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """Verify user has admin privileges"""
    # For now, check hardcoded admin list
    # Future: check user.role == "admin"
    if user_id not in ["admin-user-id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user_id
```

## Success Criteria

- [ ] Admin API routes for flags CRUD created
- [ ] Merge/split endpoints functional
- [ ] Outlier detection algorithm working
- [ ] Admin page route created with authentication
- [ ] Cleanup Queue UI displays pending flags
- [ ] Merge preview shows expected results
- [ ] Split action creates new products
- [ ] Outlier badges displayed with severity levels
- [ ] Admin workflow end-to-end tested
- [ ] Authentication guards admin routes
- [ ] <5 min to review 20 flagged items
- [ ] Stats dashboard shows pending/approved/rejected counts
