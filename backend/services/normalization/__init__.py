"""Normalization services package"""
from .matcher import ProductMatcher
from .scorer import ConfidenceScorer
from .flag_processor import ScraperFlagProcessor
from .weight_parser import parse_weight, extract_weight_from_name

__all__ = [
    "ProductMatcher",
    "ConfidenceScorer",
    "ScraperFlagProcessor",
    "parse_weight",
    "extract_weight_from_name",
]
