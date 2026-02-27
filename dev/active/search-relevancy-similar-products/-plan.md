# Search Relevancy & Similar Products

## Changes Made

### 1. Search Relevancy (`backend/routers/search.py`)
- Added ILIKE pre-filter: splits query into words, only loads products containing at least one word
- Switched from `fuzz.token_sort_ratio` to `fuzz.WRatio` (multi-strategy scorer)
- Added exact-substring bonus (+0.15 if query appears verbatim in product name)
- Raised minimum threshold from 0.30 to 0.40

### 2. Related Products Endpoint (`backend/routers/products.py`)
- Replaced simple brand/type filter with fuzzy WRatio scoring against same-type products
- Returns top 8 most similar products with similarity_score >= 0.60
- Includes similarity_score in response
- Resolves variant to master product automatically

### 3. Product Detail Page (`frontend/app/products/[id]/page.tsx`)
- Added RelatedProduct interface and state
- Fetches related products via existing `api.products.getRelated()`
- Replaced placeholder with responsive 2x4 cards grid
- Cards show: name, brand, type badge, THC/CBD, price range
- Section hidden entirely when no similar products found
