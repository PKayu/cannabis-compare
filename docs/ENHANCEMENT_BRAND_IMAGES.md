# Enhancement: Brand Images with Proper Licensing

**Status**: Future Enhancement (Low Priority)
**Phase**: Post-MVP (Phase 4 or later)
**Legal Review**: Required before implementation

---

## Context & Motivation

Currently, the app displays product information (name, strain type, price, THC %) without brand/product images. Adding visual brand recognition would improve:
- User experience and product discovery
- Brand trust and legitimacy
- Mobile experience (visual scanning easier than text)

However, brand images are copyright/trademark protected. This plan ensures legal compliance before implementation.

---

## Phase Breakdown

### Phase 1: Legal & Partnership Preparation (2-4 weeks)

**Goal**: Establish legal framework and identify image sources

**Tasks**:
1. **Legal Review**
   - Consult with attorney specializing in IP law
   - Document fair use limitations for cannabis industry
   - Create image licensing policy document
   - Establish brand contact email/process

2. **Identify Image Sources (Priority Order)**
   - [ ] Leafly API or similar licensed cannabis data provider
   - [ ] Direct brand partnerships (contact Utah cannabis brands)
   - [ ] Dispensary partnerships (request image licensing)
   - [ ] Public domain or creative commons alternatives
   - [ ] User-generated photo uploads as fallback

3. **Create Brand Contact Template**
   - Professional outreach email template
   - Image usage rights request form
   - Standard licensing agreement (if needed)
   - Track contact attempts and responses

**Deliverables**:
- Legal compliance document
- Image source priority list with contact info
- Brand outreach templates

---

### Phase 2: Database Schema Updates (1 week)

**Goal**: Prepare database to store image metadata and licensing info

**Changes to `backend/models.py`**:
```python
# Add to Product model
class Product(Base):
    __tablename__ = "products"

    # ... existing fields ...

    # New image fields
    image_url: str | None = Column(String, nullable=True)
    image_source: str | None = Column(String, nullable=True)  # "brand", "dispensary", "user", "api"
    image_license_type: str | None = Column(String, nullable=True)  # "direct_grant", "fair_use", "api", "ugc"
    image_license_expiry: datetime | None = Column(DateTime, nullable=True)
    image_attribution_required: bool = Column(Boolean, default=False)
    image_usage_notes: str | None = Column(String, nullable=True)

# New model for tracking brand partnerships
class BrandPartnership(Base):
    __tablename__ = "brand_partnerships"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    brand_id: UUID = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    contact_email: str = Column(String)
    contact_name: str = Column(String, nullable=True)
    status: str = Column(String)  # "pending", "approved", "rejected", "expired"
    image_rights_granted: bool = Column(Boolean, default=False)
    agreement_url: str | None = Column(String, nullable=True)
    partnership_start_date: datetime | None = Column(DateTime, nullable=True)
    partnership_expiry_date: datetime | None = Column(DateTime, nullable=True)
    notes: str | None = Column(String, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Tasks**:
- [ ] Create Alembic migration for new columns
- [ ] Create BrandPartnership model and migration
- [ ] Update related Pydantic schemas in `backend/schemas/`
- [ ] Test database updates locally

**Deliverables**:
- Database migrations
- Updated schema documentation

---

### Phase 3: Image Management System (2-3 weeks)

**Goal**: Build backend infrastructure for storing, serving, and tracking images

**Backend Implementation** (`backend/services/image_manager.py`):
```python
# Pseudo-code for image management service

class ImageManager:
    """Handles image storage, validation, and licensing compliance."""

    async def fetch_and_store_brand_image(
        self,
        brand_id: str,
        image_url: str,
        source: str,
        license_type: str
    ) -> dict:
        """Download image from source, validate, and store."""
        # 1. Validate image URL (security check)
        # 2. Download image with retry logic
        # 3. Store to cloud storage (S3, Cloudinary, etc.)
        # 4. Generate thumbnail
        # 5. Update database with image metadata
        # 6. Return public image URL
        pass

    async def validate_licensing(self, product_id: str) -> bool:
        """Check if image license is still valid (not expired)."""
        # 1. Query product image_license_expiry
        # 2. Return True if not expired
        # 3. Mark for renewal if approaching expiry
        pass

    async def handle_license_expiry(self, product_id: str) -> None:
        """Fallback when license expires (remove image or mark for renewal)."""
        # 1. Remove image_url from product
        # 2. Notify admin
        # 3. Queue for re-licensing request
        pass
```

**Cloud Storage Setup**:
- [ ] Choose provider (Cloudinary, AWS S3, or Supabase Storage)
- [ ] Configure image optimization pipeline
- [ ] Set up CDN for fast image delivery
- [ ] Establish backup/retention policy

**New API Endpoints** (`backend/routers/images.py`):
```
GET /api/images/{product_id}           # Get product image + metadata
POST /api/admin/images/fetch/{brand_id} # Admin: trigger image fetch from brand
GET /api/admin/brands/partnerships      # View brand partnership status
POST /api/admin/brands/{brand_id}/approve # Approve brand partnership
```

**Tasks**:
- [ ] Set up cloud storage integration
- [ ] Build ImageManager service
- [ ] Create image validation and optimization
- [ ] Create admin endpoints for image management
- [ ] Implement license expiry checking (background job)
- [ ] Add error handling for failed image fetches

**Deliverables**:
- Image management service
- Cloud storage configuration
- Admin API endpoints
- Background job for license expiry

---

### Phase 4: Frontend Integration (1-2 weeks)

**Goal**: Display images on frontend with attribution/licensing info

**Component Updates** (`frontend/components/ProductCard.tsx`):
```tsx
interface ProductCardProps {
  product: Product & { image_url?: string; image_attribution_required?: boolean }
}

export function ProductCard({ product }: ProductCardProps) {
  return (
    <div className="border rounded p-4">
      {product.image_url && (
        <div className="relative">
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-48 object-cover rounded"
          />
          {product.image_attribution_required && (
            <span className="text-xs text-gray-500 mt-1">
              Image provided by {product.image_source}
            </span>
          )}
        </div>
      )}
      <h3 className="font-bold mt-4">{product.name}</h3>
      {/* ... rest of product info ... */}
    </div>
  )
}
```

**Tasks**:
- [ ] Update ProductCard to display images
- [ ] Add image fallback (placeholder if no image)
- [ ] Add attribution text where required
- [ ] Test image loading performance
- [ ] Mobile responsiveness check

**Deliverables**:
- Updated product display components
- Image attribution system

---

### Phase 5: Brand Outreach & Partnerships (Ongoing)

**Goal**: Secure image licensing from brands

**Process**:
1. Generate list of brands in database
2. Use contact template to reach out
3. Track partnership status in database
4. Collect signed agreements
5. Update image sources as partnerships approved

**Admin Tools Needed**:
- Partnership status dashboard
- Bulk outreach email template generator
- Partnership renewal reminders

---

## Technical Decisions

### Image Storage Location
- **Option A**: Cloud CDN (Cloudinary) - Best for optimization
- **Option B**: AWS S3 + CloudFront - Most control, higher cost
- **Option C**: Supabase Storage - Integrated with current stack
- **Recommendation**: Cloudinary (free tier, auto-optimization, easy CDN)

### Image Licensing Compliance
- Store source and license type for each image
- Implement expiry dates for partnerships
- Add admin dashboard to monitor licensing status
- Log all image usage for audit trail

### Fallback Strategy
- If no brand image available: show generic product image or placeholder
- If license expires: remove image, queue for renewal
- Never display image without proper licensing documented

---

## Success Criteria

- [ ] Database supports image metadata and licensing info
- [ ] Images served from CDN with fast load times
- [ ] All displayed images have documented legal source
- [ ] Brand partnerships tracked in admin dashboard
- [ ] License expiry checked automatically
- [ ] Frontend displays images with attribution where required
- [ ] No copyright/trademark violations occur
- [ ] User feedback shows improved product recognition

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Legal challenge on image usage | Get written permission from brands; document fair use rationale with attorney |
| License expiry not caught | Automated background job checks expiry weekly; admin alerts |
| Images slow down page load | Use CDN, optimize size, lazy load images |
| Brands revoke permission | Have fallback plan (remove image, show placeholder) |
| Broken image links | Implement retry logic, monitor with error tracking |

---

## Timeline & Phasing

**Recommended Order** (for maximum value):
1. **Phase 1** (Weeks 1-4): Legal prep + brand research
2. **Phase 2** (Week 5): Database updates
3. **Phase 3** (Weeks 6-8): Image management system
4. **Phase 4** (Weeks 9-10): Frontend integration
5. **Phase 5** (Ongoing): Brand outreach

**Earliest Start**: After Phase 3 MVP completion (current work)

---

## Dependencies

- Legal consultation (external)
- Brand contact information (requires research)
- Cloud storage account (free tier available)
- Admin dashboard (needed to manage partnerships)

---

## Notes

- This is a *low-priority enhancement* — MVP functionality is complete without images
- Start with Phase 1 (legal) to de-risk the project
- Phase 5 (brand outreach) is ongoing; can happen in parallel once infrastructure is ready
- Consider starting with user-generated product photos as faster alternative
