"""
LLM provider interface and implementations for dispensary discovery.

Supports multiple LLM providers for flexibility and cost optimization.
"""

from abc import ABC, abstractmethod
from typing import Optional
import base64
import json
from pathlib import Path

from services.discovery.models import LLMAnalysisResult


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def analyze_screenshot(
        self,
        screenshot_path: str,
        html_content: Optional[str] = None,
        prompt: str = ""
    ) -> LLMAnalysisResult:
        """
        Analyze screenshot/HTML and extract product structure.

        Args:
            screenshot_path: Path to screenshot image
            html_content: Optional HTML content for supplementary context
            prompt: Analysis prompt

        Returns:
            LLMAnalysisResult with field maps and selectors
        """
        pass

    @abstractmethod
    def get_cost_estimate(self) -> float:
        """Estimate cost per analysis in USD."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini provider (free tier)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "models/gemini-2.5-flash"  # Latest Gemini Flash with vision

    async def analyze_screenshot(
        self,
        screenshot_path: str,
        html_content: Optional[str] = None,
        prompt: str = ""
    ) -> LLMAnalysisResult:
        """Analyze screenshot using Gemini vision model."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package required. "
                "Install with: pip install google-generativeai"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Read screenshot image
        with open(screenshot_path, 'rb') as f:
            image_data = f.read()

        # Create vision model
        model = genai.GenerativeModel(self.model)

        # Build enhanced prompt with HTML context if available
        full_prompt = prompt
        if html_content:
            # Truncate HTML to avoid token limits (keep first 30000 chars for better context)
            html_snippet = html_content[:30000]
            full_prompt += f"\n\nHTML Context (first 30k chars - use this as PRIMARY source for selectors):\n```html\n{html_snippet}\n```"

        full_prompt += """

Please return your analysis as a JSON object with this exact structure:
{
  "field_map": {
    "name": {"selector": ".product-name", "pattern": "direct", "coverage": 100},
    "price": {"selector": ".price", "pattern": "$XX.XX", "coverage": 100},
    ...
  },
  "product_structure": "Description of overall HTML structure",
  "css_selectors": {
    "container": ".product-item",
    "name": ".product-name",
    "price": ".price",
    ...
  },
  "extraction_patterns": {
    "weight": "(\\\\d+\\\\.?\\\\d*)\\\\s*(g|oz|mg)",
    "thc": "(\\\\d+\\\\.?\\\\d*)%\\\\s*THC",
    ...
  },
  "edge_cases": [
    "Weight is embedded in product name, not separate field",
    "Some products lack CBD data",
    ...
  ],
  "confidence": 0.85
}

Return ONLY the JSON object, no additional text.
"""

        # Generate analysis
        response = model.generate_content([
            {
                "mime_type": "image/png",
                "data": base64.b64encode(image_data).decode()
            },
            full_prompt
        ])

        # Parse JSON response
        response_text = response.text.strip()

        # Try to extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            analysis = json.loads(response_text)
        except json.JSONDecodeError as e:
            # Fallback: create basic structure from text response
            print(f"[WARNING] Failed to parse JSON from Gemini response: {e}")
            print(f"Response: {response_text[:500]}")
            analysis = {
                "field_map": {},
                "product_structure": response_text,
                "css_selectors": {},
                "extraction_patterns": {},
                "edge_cases": ["Failed to parse structured response"],
                "confidence": 0.5
            }

        # Create LLMAnalysisResult
        return LLMAnalysisResult(
            field_map=analysis.get("field_map", {}),
            product_structure=analysis.get("product_structure", ""),
            css_selectors=analysis.get("css_selectors", {}),
            extraction_patterns=analysis.get("extraction_patterns", {}),
            edge_cases=analysis.get("edge_cases", []),
            confidence=analysis.get("confidence", 0.0)
        )

    def get_cost_estimate(self) -> float:
        """Gemini free tier is $0."""
        return 0.0


class GLMProvider(LLMProvider):
    """GLM (General Language Model) provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.model = "glm-4v-plus"  # Vision model

    async def analyze_screenshot(
        self,
        screenshot_path: str,
        html_content: Optional[str] = None,
        prompt: str = ""
    ) -> LLMAnalysisResult:
        """Analyze screenshot using GLM vision model."""
        # TODO: Implement GLM API integration
        raise NotImplementedError("GLM provider not yet implemented")

    def get_cost_estimate(self) -> float:
        """GLM estimated cost."""
        return 0.01


class CodexProvider(LLMProvider):
    """OpenAI Codex/GPT-4V provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gpt-4-vision-preview"

    async def analyze_screenshot(
        self,
        screenshot_path: str,
        html_content: Optional[str] = None,
        prompt: str = ""
    ) -> LLMAnalysisResult:
        """Analyze screenshot using OpenAI GPT-4V."""
        # TODO: Implement OpenAI API integration
        raise NotImplementedError("Codex provider not yet implemented")

    def get_cost_estimate(self) -> float:
        """OpenAI estimated cost."""
        return 0.05


class ClaudeProvider(LLMProvider):
    """Claude API provider (fallback)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "claude-3-5-sonnet-20241022"

    async def analyze_screenshot(
        self,
        screenshot_path: str,
        html_content: Optional[str] = None,
        prompt: str = ""
    ) -> LLMAnalysisResult:
        """Analyze screenshot using Claude API."""
        # TODO: Implement Claude API integration
        raise NotImplementedError("Claude provider not yet implemented")

    def get_cost_estimate(self) -> float:
        """Claude estimated cost."""
        return 0.10
