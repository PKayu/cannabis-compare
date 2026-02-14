"""
Data models for dispensary discovery framework.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class LLMAnalysisResult:
    """Standardized result from LLM analysis of dispensary page."""

    field_map: Dict[str, Dict[str, Any]]  # field_name -> {selector, pattern, coverage}
    product_structure: str  # Description of HTML structure
    css_selectors: Dict[str, str]  # field_name -> css_selector
    extraction_patterns: Dict[str, str]  # field_name -> regex/pattern
    edge_cases: List[str]  # Notes about special handling
    confidence: float  # 0-1 confidence in analysis


@dataclass
class DiscoveryResult:
    """Complete discovery result for a dispensary website."""

    url: str
    dispensary_name: str
    timestamp: datetime
    screenshot_path: str
    html_path: str
    field_map: Dict[str, Dict[str, Any]]
    css_selectors: Dict[str, str]
    extraction_patterns: Dict[str, str]
    edge_cases: List[str]
    llm_provider: str  # Name of LLM provider used
    analysis_cost: float  # Estimated cost in USD
