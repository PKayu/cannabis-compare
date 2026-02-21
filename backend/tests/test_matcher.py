"""
Tests for ProductMatcher fuzzy matching logic.

Run with: pytest backend/tests/test_matcher.py -v
"""
import pytest
from services.normalization.matcher import ProductMatcher


class TestProductMatcher:
    """Test cases for ProductMatcher class"""

    def test_exact_match_high_confidence(self):
        """Exact matches should return >90% confidence"""
        score, match_type = ProductMatcher.score_match(
            scraped_name="Gorilla Glue #4",
            master_name="Gorilla Glue #4",
            scraped_brand="Tryke",
            master_brand="Tryke",
            scraped_thc=24.5,
            master_thc=24.5
        )

        assert score >= 0.90
        assert match_type == "auto_merge"

    def test_similar_name_auto_merge(self):
        """Similar names with same brand should auto-merge or be new product"""
        score, match_type = ProductMatcher.score_match(
            scraped_name="GG4 (Gorilla Glue #4)",
            master_name="Gorilla Glue #4",
            scraped_brand="Tryke",
            master_brand="Tryke",
            scraped_thc=24.0,
            master_thc=24.5
        )

        # Should be high — only two outcomes now: auto_merge or new_product
        assert score >= 0.60
        assert match_type in ["auto_merge", "new_product"]

    def test_different_brand_lowers_score(self):
        """Different brand should lower confidence score"""
        same_brand_score, _ = ProductMatcher.score_match(
            scraped_name="Gorilla Glue #4",
            master_name="Gorilla Glue #4",
            scraped_brand="Tryke",
            master_brand="Tryke"
        )

        diff_brand_score, _ = ProductMatcher.score_match(
            scraped_name="Gorilla Glue #4",
            master_name="Gorilla Glue #4",
            scraped_brand="Different Brand",
            master_brand="Tryke"
        )

        assert same_brand_score > diff_brand_score

    def test_very_different_names_low_confidence(self):
        """Very different names should return <60% confidence"""
        score, match_type = ProductMatcher.score_match(
            scraped_name="Blue Dream",
            master_name="OG Kush",
            scraped_brand="Brand A",
            master_brand="Brand B"
        )

        assert score < 0.60
        assert match_type == "new_product"

    def test_medium_confidence_now_new_product(self):
        """Medium confidence (60-90%) should now be new_product, not flagged_review"""
        score, match_type = ProductMatcher.score_match(
            scraped_name="Blue Dream Haze",
            master_name="Blue Dream",
            scraped_brand="WholesomeCo",
            master_brand="WholesomeCo"
        )

        # Partial match: below 90% is now new_product (no more flagged_review)
        assert score < 0.90
        assert match_type == "new_product"

    def test_normalize_product_name_removes_symbols(self):
        """Normalization should remove trademark symbols"""
        normalized = ProductMatcher.normalize_product_name("Gorilla Glue® #4™")

        assert "®" not in normalized
        assert "™" not in normalized
        assert "gorilla glue" in normalized

    def test_normalize_product_name_removes_weight(self):
        """Normalization should remove weight suffixes"""
        normalized = ProductMatcher.normalize_product_name("Blue Dream 3.5g")

        assert "3.5g" not in normalized
        assert "blue dream" in normalized

    def test_normalize_brand_removes_llc(self):
        """Brand normalization should remove LLC, Inc., etc."""
        normalized = ProductMatcher.normalize_brand_name("WholesomeCo LLC")

        assert "llc" not in normalized
        assert "wholesomeco" in normalized

    def test_thc_similarity_close_values(self):
        """THC weight is 0.00 so THC values do not affect the match score"""
        score1, _ = ProductMatcher.score_match(
            scraped_name="Test Product",
            master_name="Test Product",
            scraped_brand="Brand",
            master_brand="Brand",
            scraped_thc=24.0,
            master_thc=24.5
        )

        score2, _ = ProductMatcher.score_match(
            scraped_name="Test Product",
            master_name="Test Product",
            scraped_brand="Brand",
            master_brand="Brand",
            scraped_thc=24.0,
            master_thc=40.0  # Very different THC — no longer penalised
        )

        # THC_WEIGHT is 0.00: scores are identical regardless of THC difference
        assert abs(score1 - score2) < 0.01

    def test_missing_thc_no_penalty(self):
        """Missing THC values should not penalize score"""
        with_thc, _ = ProductMatcher.score_match(
            scraped_name="Test Product",
            master_name="Test Product",
            scraped_brand="Brand",
            master_brand="Brand",
            scraped_thc=24.0,
            master_thc=24.0
        )

        without_thc, _ = ProductMatcher.score_match(
            scraped_name="Test Product",
            master_name="Test Product",
            scraped_brand="Brand",
            master_brand="Brand",
            scraped_thc=None,
            master_thc=None
        )

        # Should be same or very close
        assert abs(with_thc - without_thc) < 0.05

    def test_find_best_match_returns_highest_score(self):
        """find_best_match should return the highest scoring candidate"""
        candidates = [
            {"id": "1", "name": "Gorilla Glue #4", "brand": "Tryke", "thc_percentage": 24.5},
            {"id": "2", "name": "Blue Dream", "brand": "WholesomeCo", "thc_percentage": 22.0},
            {"id": "3", "name": "OG Kush", "brand": "Dragonfly", "thc_percentage": 26.0},
        ]

        best_match, score, match_type = ProductMatcher.find_best_match(
            scraped_name="Gorilla Glue",
            scraped_brand="Tryke",
            candidates=candidates,
            scraped_thc=24.0
        )

        assert best_match is not None
        assert best_match["id"] == "1"  # Should match Gorilla Glue #4

    def test_find_best_match_respects_min_threshold(self):
        """find_best_match should respect minimum threshold"""
        candidates = [
            {"id": "1", "name": "Completely Different Product", "brand": "Other Brand", "thc_percentage": 15.0},
        ]

        best_match, score, match_type = ProductMatcher.find_best_match(
            scraped_name="Gorilla Glue #4",
            scraped_brand="Tryke",
            candidates=candidates,
            scraped_thc=24.0,
            min_threshold=0.70  # High threshold
        )

        # No match should meet threshold
        assert best_match is None
        assert score == 0.0

    def test_threshold_description(self):
        """get_threshold_description should return correct descriptions"""
        high = ProductMatcher.get_threshold_description(0.95)
        medium = ProductMatcher.get_threshold_description(0.75)
        low = ProductMatcher.get_threshold_description(0.40)

        assert "Auto-merge" in high
        assert "New product" in medium  # No more "review" — medium is now new_product
        assert "New product" in low


class TestProductMatcherEdgeCases:
    """Edge case tests for ProductMatcher"""

    def test_empty_name_handling(self):
        """Empty names should return low score"""
        score, match_type = ProductMatcher.score_match(
            scraped_name="",
            master_name="Gorilla Glue #4",
            scraped_brand="Tryke",
            master_brand="Tryke"
        )

        assert score < 0.60
        assert match_type == "new_product"

    def test_unicode_characters_in_names(self):
        """Unicode characters should be handled properly"""
        score, match_type = ProductMatcher.score_match(
            scraped_name="Açaí Kush™",
            master_name="Acai Kush",
            scraped_brand="Brand",
            master_brand="Brand"
        )

        # Should still get reasonable match
        assert score > 0.50

    def test_case_insensitive_matching(self):
        """Matching should be case insensitive"""
        score1, _ = ProductMatcher.score_match(
            scraped_name="GORILLA GLUE #4",
            master_name="gorilla glue #4",
            scraped_brand="TRYKE",
            master_brand="tryke"
        )

        score2, _ = ProductMatcher.score_match(
            scraped_name="Gorilla Glue #4",
            master_name="Gorilla Glue #4",
            scraped_brand="Tryke",
            master_brand="Tryke"
        )

        assert score1 == score2
