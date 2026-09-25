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
        )

        assert score >= 0.90
        assert match_type == "auto_merge"

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
        """Very different names should return <65% confidence"""
        score, match_type = ProductMatcher.score_match(
            scraped_name="Blue Dream",
            master_name="OG Kush",
            scraped_brand="Brand A",
            master_brand="Brand B"
        )

        assert score < 0.65
        assert match_type == "new_product"

    def test_find_best_match_returns_highest_score(self):
        """find_best_match should return the highest scoring candidate"""
        candidates = [
            {"id": "1", "name": "Gorilla Glue #4", "brand": "Tryke"},
            {"id": "2", "name": "Blue Dream", "brand": "WholesomeCo"},
            {"id": "3", "name": "OG Kush", "brand": "Dragonfly"},
        ]

        best_match, score, match_type = ProductMatcher.find_best_match(
            scraped_name="Gorilla Glue",
            scraped_brand="Tryke",
            candidates=candidates,
        )

        assert best_match is not None
        assert best_match["id"] == "1"  # Should match Gorilla Glue #4

    def test_find_best_match_respects_min_threshold(self):
        """find_best_match should respect minimum threshold"""
        candidates = [
            {"id": "1", "name": "Completely Different Product", "brand": "Other Brand"},
        ]

        best_match, score, match_type = ProductMatcher.find_best_match(
            scraped_name="Gorilla Glue #4",
            scraped_brand="Tryke",
            candidates=candidates,
            min_threshold=0.70  # High threshold
        )

        # No match should meet threshold
        assert best_match is None
        assert score == 0.0

    def test_find_best_match_strict_category_filter(self):
        """No cross-category matching: identical names in another category
        must not match — an empty same-category pool means new product."""
        candidates = [
            {"id": "1", "name": "Blue Dream", "brand": "Tryke", "product_type": "edible"},
        ]

        best_match, score, match_type = ProductMatcher.find_best_match(
            scraped_name="Blue Dream",
            scraped_brand="Tryke",
            candidates=candidates,
            product_type="flower",
        )

        assert best_match is None
        assert match_type == "new_product"

    def test_find_best_match_unknown_category_searches_all(self):
        """Products with generic/unknown category still search all candidates"""
        candidates = [
            {"id": "1", "name": "Blue Dream", "brand": "Tryke", "product_type": "edible"},
        ]

        best_match, _, _ = ProductMatcher.find_best_match(
            scraped_name="Blue Dream",
            scraped_brand="Tryke",
            candidates=candidates,
            product_type="unknown",
        )

        assert best_match is not None

    def test_threshold_description(self):
        """get_threshold_description should return correct descriptions"""
        high = ProductMatcher.get_threshold_description(0.95)
        medium = ProductMatcher.get_threshold_description(0.75)
        low = ProductMatcher.get_threshold_description(0.40)

        assert "Auto-merge" in high
        assert "Near-miss" in medium
        assert "New product" in low


class TestWeightSignal:
    """Weight-match scoring signal + renormalization"""

    def test_weight_absent_reproduces_name_brand_split(self):
        """With no weight data, score must equal the historical 0.75/0.25 blend"""
        score_no_weight, _ = ProductMatcher.score_match(
            scraped_name="Blue Dream Haze",
            master_name="Blue Dream",
            scraped_brand="Tryke",
            master_brand="Tryke",
        )

        # Renormalized 0.60/0.25 == 0.75/0.25 split
        from rapidfuzz import fuzz
        name_sim = fuzz.token_sort_ratio(
            ProductMatcher.normalize_product_name("Blue Dream Haze"),
            ProductMatcher.normalize_product_name("Blue Dream"),
        ) / 100.0
        expected = (name_sim * 0.75) + (1.0 * 0.25)
        assert score_no_weight == pytest.approx(expected, abs=0.001)

    def test_matching_weight_boosts_score(self):
        """A matching weight should raise the score vs a mismatched weight"""
        matched, _ = ProductMatcher.score_match(
            scraped_name="Blue Dream Haze",
            master_name="Blue Dream",
            scraped_brand="Tryke",
            master_brand="Tryke",
            scraped_weight_g=3.5,
            candidate_weight_set={3.5, 7.0},
        )
        mismatched, _ = ProductMatcher.score_match(
            scraped_name="Blue Dream Haze",
            master_name="Blue Dream",
            scraped_brand="Tryke",
            master_brand="Tryke",
            scraped_weight_g=1.0,
            candidate_weight_set={3.5, 7.0},
        )

        assert matched > mismatched

    def test_weight_tolerance_covers_oz_rounding(self):
        """3.5 vs 3.54 (eighth-oz rounding) counts as a weight match"""
        sim = ProductMatcher._calculate_weight_similarity(3.5, {3.54})
        assert sim == 1.0

    def test_weight_signal_absent_when_missing(self):
        """Signal is absent (None) when either side lacks weight data"""
        assert ProductMatcher._calculate_weight_similarity(None, {3.5}) is None
        assert ProductMatcher._calculate_weight_similarity(3.5, None) is None
        assert ProductMatcher._calculate_weight_similarity(3.5, set()) is None

    def test_weight_mismatch_is_zero(self):
        assert ProductMatcher._calculate_weight_similarity(1.0, {3.5, 7.0}) == 0.0

    def test_find_best_match_passes_weight(self):
        """find_best_match should prefer the candidate with a matching weight"""
        candidates = [
            {"id": "a", "name": "Blue Dream", "brand": "Tryke", "weight_grams_set": {1.0}},
            {"id": "b", "name": "Blue Dream", "brand": "Tryke", "weight_grams_set": {3.5}},
        ]
        best_match, _, _ = ProductMatcher.find_best_match(
            scraped_name="Blue Dream",
            scraped_brand="Tryke",
            candidates=candidates,
            scraped_weight_g=3.5,
        )
        assert best_match["id"] == "b"


class TestBrandNormalization:
    """normalize_brand_name: word-boundary suffixes, punctuation, aliases"""

    def test_removes_llc_suffix(self):
        assert ProductMatcher.normalize_brand_name("Zion Cultivars, LLC") == \
            ProductMatcher.normalize_brand_name("Zion Cultivars")

    def test_removes_inc_suffix_word_boundary_only(self):
        """'Inc' stripped as a word — 'Incredibles' must survive intact"""
        assert ProductMatcher.normalize_brand_name("Incredibles") == "incredibles"
        assert ProductMatcher.normalize_brand_name("Acme Inc.") == "acme"
        assert ProductMatcher.normalize_brand_name("Acme, Inc") == "acme"

    def test_co_suffix_word_boundary(self):
        """'Co' stripped as a word — 'WholesomeCo' keeps its trailing co"""
        assert "wholesomeco" in ProductMatcher.normalize_brand_name("WholesomeCo")
        assert ProductMatcher.normalize_brand_name("Fictional Farms Co.") == \
            ProductMatcher.normalize_brand_name("Fictional Farms")

    def test_punctuation_stripped(self):
        assert ProductMatcher.normalize_brand_name("Bee-hive's!") == \
            ProductMatcher.normalize_brand_name("Bee hive s")

    def test_alias_resolution(self):
        """Known variants resolve to one canonical form"""
        assert ProductMatcher.normalize_brand_name("Wholesome Co") == \
            ProductMatcher.normalize_brand_name("WholesomeCo")
        assert ProductMatcher.normalize_brand_name("Dragonfly") == \
            ProductMatcher.normalize_brand_name("Dragonfly Wellness")

    def test_empty_brand(self):
        assert ProductMatcher.normalize_brand_name("") == ""
        assert ProductMatcher.normalize_brand_name(None) == ""


class TestNameNormalization:
    """normalize_product_name: punctuation, whitespace, synonyms, weights"""

    def test_removes_trademark_symbols(self):
        normalized = ProductMatcher.normalize_product_name("Gorilla Glue® #4™")
        assert "®" not in normalized
        assert "™" not in normalized
        assert "gorilla glue" in normalized

    def test_keeps_strain_number_hash(self):
        assert "#4" in ProductMatcher.normalize_product_name("Gorilla Glue #4")

    def test_removes_weight_suffix(self):
        normalized = ProductMatcher.normalize_product_name("Blue Dream 3.5g")
        assert "3.5g" not in normalized
        assert "blue dream" in normalized

    def test_punctuation_and_whitespace_collapse(self):
        assert ProductMatcher.normalize_product_name("Blue   Dream - Haze / OG") == \
            "blue dream haze og"

    def test_form_word_synonyms(self):
        assert ProductMatcher.normalize_product_name("Blue Dream Cartridge") == \
            ProductMatcher.normalize_product_name("Blue Dream Cart")
        assert ProductMatcher.normalize_product_name("Blue Dream Pre-Roll") == \
            ProductMatcher.normalize_product_name("Blue Dream Preroll")


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

        assert score < 0.65
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
