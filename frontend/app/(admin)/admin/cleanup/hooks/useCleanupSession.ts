export interface MatchedProduct {
  id: string
  name: string
  product_type: string | null
  brand: string | null
  brand_id: string | null
  thc_percentage: number | null
  cbd_percentage: number | null
}

export interface ScraperFlag {
  id: string
  original_name: string
  original_thc: number | null
  original_cbd: number | null
  original_thc_content: string | null  // Plain-text display: "15.4%" or "396mg"
  original_cbd_content: string | null
  original_weight: string | null
  original_price: number | null
  original_category: string | null
  original_url: string | null
  brand_name: string
  dispensary_id: string
  dispensary_name: string | null
  matched_product_id: string | null
  matched_product: MatchedProduct | null
  confidence_score: number
  confidence_percent: string
  merge_reason: string | null
  flag_type: 'match_review' | 'data_cleanup'
  status: 'pending' | 'approved' | 'rejected' | 'dismissed' | 'merged' | 'auto_merged' | 'cleaned'
  corrections: Record<string, any> | null
  issue_tags: string[] | null
  created_at: string
  updated_at: string
}

export interface FlagStats {
  pending: number
  pending_cleanup: number
  pending_review: number
  approved: number
  rejected: number
  dismissed: number
  cleaned: number
  merged: number
  total: number
}

export interface EditableFields {
  name: string
  brand_name: string
  product_type: string
  thc_percentage: string
  cbd_percentage: string
  weight: string
  price: string
}
