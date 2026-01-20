---
description: Create dispensary listing pages with map integration, inventory display, current promotions, and recurring deals calendar.
auto_execution_mode: 1
---

## Context

This workflow creates dispensary discovery features:
- Dispensary listing with map view
- Individual dispensary detail pages
- Current inventory for each pharmacy
- Recurring deals calendar (Medical Mondays, etc.)
- Hours and location information

## Steps

### 1. Create Dispensary Listing API Endpoint

Create `backend/routers/dispensaries.py`:

```python
"""Dispensary endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import Dispensary, Price

router = APIRouter(prefix="/api/dispensaries", tags=["dispensaries"])

@router.get("/")
async def list_dispensaries(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """List all Utah dispensaries with inventory counts"""

    dispensaries = db.query(Dispensary).offset(skip).limit(limit).all()

    results = []
    for disp in dispensaries:
        product_count = db.query(Price).filter(
            Price.dispensary_id == disp.id,
            Price.in_stock == True
        ).distinct(Price.product_id).count()

        results.append({
            "id": disp.id,
            "name": disp.name,
            "location": disp.location,
            "website": disp.website,
            "product_count": product_count,
            "created_at": disp.created_at
        })

    return results
```

### 2. Build Dispensary Detail API Endpoint

Add to `backend/routers/dispensaries.py`:

```python
@router.get("/{dispensary_id}")
async def get_dispensary_detail(
    dispensary_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed dispensary information"""

    disp = db.query(Dispensary).filter(Dispensary.id == dispensary_id).first()
    if not disp:
        raise HTTPException(status_code=404, detail="Dispensary not found")

    # Get current inventory
    prices = db.query(Price).filter(
        Price.dispensary_id == dispensary_id,
        Price.in_stock == True
    ).all()

    # Get active promotions
    from datetime import datetime
    from sqlalchemy import and_, or_

    promotions = db.query(Promotion).filter(
        and_(
            Promotion.dispensary_id == dispensary_id,
            Promotion.is_active == True,
            Promotion.start_date <= datetime.utcnow(),
            or_(
                Promotion.end_date == None,
                Promotion.end_date > datetime.utcnow()
            )
        )
    ).all()

    return {
        "id": disp.id,
        "name": disp.name,
        "location": disp.location,
        "website": disp.website,
        "product_count": len(prices),
        "promotions": [
            {
                "title": p.title,
                "discount_percent": p.discount_percentage,
                "day": p.recurring_day if p.is_recurring else None
            }
            for p in promotions
        ],
        "coordinates": extract_coordinates(disp.location)  # Lat/Long for maps
    }
```

### 3. Create Dispensary Listing Page

Create `frontend/app/dispensaries/page.tsx`:

```typescript
'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import DispensaryMap from '@/components/DispensaryMap'
import DispensaryList from '@/components/DispensaryList'

export default function DispensariesPage() {
  const [dispensaries, setDispensaries] = useState([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('map') // 'map' or 'list'

  useEffect(() => {
    loadDispensaries()
  }, [])

  const loadDispensaries = async () => {
    try {
      const res = await api.get('/api/dispensaries')
      setDispensaries(res.data)
    } catch (error) {
      console.error('Failed to load dispensaries:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold mb-4 text-cannabis-700">Utah Dispensaries</h1>

        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setViewMode('map')}
            className={`px-4 py-2 rounded ${viewMode === 'map' ? 'bg-cannabis-600 text-white' : 'bg-white'}`}
          >
            Map View
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-4 py-2 rounded ${viewMode === 'list' ? 'bg-cannabis-600 text-white' : 'bg-white'}`}
          >
            List View
          </button>
        </div>

        {loading ? (
          <div>Loading dispensaries...</div>
        ) : viewMode === 'map' ? (
          <DispensaryMap dispensaries={dispensaries} />
        ) : (
          <DispensaryList dispensaries={dispensaries} />
        )}
      </div>
    </div>
  )
}
```

### 4. Add Map Integration (Google Maps or Mapbox)

Create `frontend/components/DispensaryMap.tsx`:

```typescript
import React from 'react'
import { GoogleMap, LoadScript, Marker, InfoWindow } from '@react-google-maps/api'

export default function DispensaryMap({ dispensaries }) {
  const [selectedMarker, setSelectedMarker] = React.useState(null)

  const mapCenter = {
    lat: 40.7608,  // Salt Lake City
    lng: -111.8910
  }

  return (
    <LoadScript googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY}>
      <GoogleMap
        mapContainerStyle={{ width: '100%', height: '500px' }}
        center={mapCenter}
        zoom={10}
      >
        {dispensaries.map((disp) => (
          <Marker
            key={disp.id}
            position={disp.coordinates || mapCenter}
            onClick={() => setSelectedMarker(disp)}
          >
            {selectedMarker?.id === disp.id && (
              <InfoWindow onCloseClick={() => setSelectedMarker(null)}>
                <div className="p-2">
                  <h3 className="font-bold">{disp.name}</h3>
                  <p className="text-sm">{disp.location}</p>
                  <p className="text-sm">{disp.product_count} products</p>
                  <a
                    href={`/dispensaries/${disp.id}`}
                    className="text-blue-600 text-sm"
                  >
                    View Details
                  </a>
                </div>
              </InfoWindow>
            )}
          </Marker>
        ))}
      </GoogleMap>
    </LoadScript>
  )
}
```

### 5. Build Dispensary Detail Page

Create `frontend/app/dispensaries/[id]/page.tsx`:

```typescript
'use client'

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { api } from '@/lib/api'
import CurrentPromotions from '@/components/CurrentPromotions'
import DispensaryInventory from '@/components/DispensaryInventory'

export default function DispensaryDetailPage() {
  const params = useParams()
  const dispensaryId = params.id as string
  const [dispensary, setDispensary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDispensaryData()
  }, [dispensaryId])

  const loadDispensaryData = async () => {
    try {
      const res = await api.get(`/api/dispensaries/${dispensaryId}`)
      setDispensary(res.data)
    } catch (error) {
      console.error('Failed to load dispensary:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading...</div>
  if (!dispensary) return <div>Dispensary not found</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-cannabis-700">{dispensary.name}</h1>
        <p className="text-gray-600 mt-2">{dispensary.location}</p>

        <div className="grid grid-cols-2 gap-4 mt-6">
          <div className="bg-white p-4 rounded">
            <p className="text-gray-600">Products in Stock</p>
            <p className="text-2xl font-bold">{dispensary.product_count}</p>
          </div>
          <div className="bg-white p-4 rounded">
            <p className="text-gray-600">Website</p>
            <a
              href={dispensary.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cannabis-600 hover:underline"
            >
              Visit Website
            </a>
          </div>
        </div>

        {dispensary.promotions.length > 0 && (
          <section className="mt-8">
            <h2 className="text-2xl font-bold mb-4">Current Promotions</h2>
            <CurrentPromotions promotions={dispensary.promotions} />
          </section>
        )}

        <section className="mt-8">
          <h2 className="text-2xl font-bold mb-4">Inventory</h2>
          <DispensaryInventory dispensaryId={dispensaryId} />
        </section>
      </div>
    </div>
  )
}
```

### 6. Display Current Promotions

Create `frontend/components/CurrentPromotions.tsx`:

```typescript
interface Promotion {
  title: string
  discount_percent: number
  day: string | null
}

export default function CurrentPromotions({ promotions }: { promotions: Promotion[] }) {
  return (
    <div className="space-y-4">
      {promotions.map((promo, idx) => (
        <div
          key={idx}
          className="bg-green-50 border-l-4 border-green-500 p-4 rounded"
        >
          <h3 className="font-bold text-green-900">{promo.title}</h3>
          <p className="text-green-700">
            {promo.discount_percent}% off
            {promo.day && ` every ${promo.day}`}
          </p>
        </div>
      ))}
    </div>
  )
}
```

### 7. Show Recurring Deals Calendar

Create `frontend/components/RecurringDealsCalendar.tsx`:

```typescript
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function RecurringDealsCalendar({ promotions }) {
  return (
    <div className="grid grid-cols-7 gap-2 mt-6">
      {DAYS.map((day) => {
        const dayPromos = promotions.filter(p => p.day?.toLowerCase() === day.toLowerCase())
        return (
          <div
            key={day}
            className={`p-4 rounded border ${dayPromos.length > 0 ? 'bg-cannabis-50 border-cannabis-300' : 'bg-gray-50'}`}
          >
            <h4 className="font-bold text-sm">{day}</h4>
            {dayPromos.map((promo, idx) => (
              <p key={idx} className="text-xs text-green-600 mt-1">
                {promo.title}
              </p>
            ))}
          </div>
        )
      })}
    </div>
  )
}
```

### 8. Add Pharmacy Details

(Already shown in dispensary detail page with location, website, product count)

## Success Criteria

- [ ] Dispensary listing API returns all dispensaries
- [ ] Dispensary detail API functional
- [ ] Dispensary listing page displays all pharmacies
- [ ] Map view shows dispensary locations
- [ ] Map markers clickable with info windows
- [ ] List view shows dispensary details
- [ ] Dispensary detail page loads correctly
- [ ] Current promotions displayed
- [ ] Recurring deals calendar shows all 7 days
- [ ] Inventory section shows products
- [ ] Website links functional
- [ ] Mobile responsive design verified
