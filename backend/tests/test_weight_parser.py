"""Tests for the weight parsing utility"""
import pytest
from services.normalization.weight_parser import parse_weight, extract_weight_from_name


class TestParseWeight:
    """Test parse_weight() function"""

    def test_grams_integer(self):
        label, grams = parse_weight("7g")
        assert label == "7g"
        assert grams == 7.0

    def test_grams_decimal(self):
        label, grams = parse_weight("3.5g")
        assert label == "3.5g"
        assert grams == 3.5

    def test_grams_with_space(self):
        label, grams = parse_weight("3.5 g")
        assert label == "3.5g"
        assert grams == 3.5

    def test_ounce(self):
        label, grams = parse_weight("1oz")
        assert label == "1oz"
        assert grams == 28.0

    def test_ounce_with_space(self):
        label, grams = parse_weight("1 oz")
        assert label == "1oz"
        assert grams == 28.0

    def test_half_ounce(self):
        label, grams = parse_weight("0.5oz")
        assert label == "0.5oz"
        assert grams == 14.0

    def test_milligrams(self):
        label, grams = parse_weight("100mg")
        assert label == "100mg"
        assert grams == 0.1

    def test_milligrams_large(self):
        label, grams = parse_weight("500mg")
        assert label == "500mg"
        assert grams == 0.5

    def test_fraction_eighth(self):
        label, grams = parse_weight("1/8 oz")
        assert label == "3.5g"
        assert grams == 3.5

    def test_fraction_quarter(self):
        label, grams = parse_weight("1/4 oz")
        assert label == "7g"
        assert grams == 7.0

    def test_fraction_half(self):
        label, grams = parse_weight("1/2 oz")
        assert label == "14g"
        assert grams == 14.0

    def test_named_eighth(self):
        label, grams = parse_weight("eighth")
        assert label == "3.5g"
        assert grams == 3.5

    def test_named_quarter(self):
        label, grams = parse_weight("quarter")
        assert label == "7g"
        assert grams == 7.0

    def test_named_half(self):
        label, grams = parse_weight("half")
        assert label == "14g"
        assert grams == 14.0

    def test_none_input(self):
        label, grams = parse_weight(None)
        assert label is None
        assert grams is None

    def test_empty_string(self):
        label, grams = parse_weight("")
        assert label is None
        assert grams is None

    def test_unparseable(self):
        label, grams = parse_weight("large")
        assert label is None
        assert grams is None

    def test_case_insensitive(self):
        label, grams = parse_weight("3.5G")
        assert label == "3.5g"
        assert grams == 3.5

    def test_ounce_uppercase(self):
        label, grams = parse_weight("1OZ")
        assert label == "1oz"
        assert grams == 28.0


class TestExtractWeightFromName:
    """Test extract_weight_from_name() function"""

    def test_weight_at_end(self):
        name, label, grams = extract_weight_from_name("Blue Dream 3.5g")
        assert "Blue Dream" in name
        assert label == "3.5g"
        assert grams == 3.5

    def test_weight_with_dash(self):
        name, label, grams = extract_weight_from_name("Blue Dream - 1oz")
        assert "Blue Dream" in name
        assert label == "1oz"
        assert grams == 28.0

    def test_no_weight_in_name(self):
        name, label, grams = extract_weight_from_name("Blue Dream")
        assert name == "Blue Dream"
        assert label is None
        assert grams is None

    def test_weight_in_parens(self):
        name, label, grams = extract_weight_from_name("Blue Dream (3.5g)")
        assert "Blue Dream" in name
        assert label == "3.5g"
        assert grams == 3.5
