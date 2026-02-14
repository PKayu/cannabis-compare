"""
Discovery framework for analyzing dispensary websites.

This package provides tools to automatically discover product structures
and generate field maps for Playwright scraper development.
"""

from services.discovery.models import DiscoveryResult, LLMAnalysisResult
from services.discovery.llm_providers import (
    LLMProvider,
    GeminiProvider,
    GLMProvider,
    CodexProvider,
    ClaudeProvider
)
from services.discovery.playwright_explorer import PlaywrightDiscoveryExplorer

__all__ = [
    'DiscoveryResult',
    'LLMAnalysisResult',
    'LLMProvider',
    'GeminiProvider',
    'GLMProvider',
    'CodexProvider',
    'ClaudeProvider',
    'PlaywrightDiscoveryExplorer'
]
