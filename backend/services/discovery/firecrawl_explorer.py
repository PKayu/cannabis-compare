"""
Firecrawl-based dispensary discovery module for scraper development.

This module provides tools for exploring dispensary websites using Firecrawl's
LLM-powered extraction to understand site structure before building Playwright scrapers.

Usage:
    from services.discovery.firecrawl_explorer import FirecrawlExplorer

    explorer = FirecrawlExplorer(api_key="fc-xxx")
    result = await explorer.discover(
        url="https://dispensary.com/menu",
        name="Dispensary Name"
    )
    explorer.save_discovery(result, "discovery_output/")
"""

import aiohttp
import json
import logging
import re
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)

# Standard extraction schema for cannabis products
CANNABIS_PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "products": {
            "type": "array",
            "description": "List of cannabis products found on the page",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full product name including strain and size"
                    },
                    "brand": {
                        "type": "string",
                        "description": "Cultivator, brand, or manufacturer name"
                    },
                    "price": {
                        "type": "number",
                        "description": "Current price in dollars (numeric only)"
                    },
                    "weight": {
                        "type": "string",
                        "description": "Weight or size like '3.5g', '1oz', '100mg', 'each'"
                    },
                    "thc_percentage": {
                        "type": "number",
                        "description": "THC content as percentage (0-100)"
                    },
                    "cbd_percentage": {
                        "type": "number",
                        "description": "CBD content as percentage (0-100)"
                    },
                    "strain_type": {
                        "type": "string",
                        "description": "Indica, Sativa, Hybrid, or single letter (I/S/H)"
                    },
                    "in_stock": {
                        "type": "boolean",
                        "description": "Whether product is currently available for purchase"
                    },
                    "url": {
                        "type": "string",
                        "description": "Direct link to product page"
                    },
                    "image_url": {
                        "type": "string",
                        "description": "Product image URL"
                    },
                    "description": {
                        "type": "string",
                        "description": "Product description or notes"
                    },
                    "batch_number": {
                        "type": "string",
                        "description": "Batch or lot number"
                    },
                    "category": {
                        "type": "string",
                        "description": "Product category: flower, vaporizer, edible, concentrate, tincture, topical, pre-roll"
                    }
                },
                "required": ["name", "price"]
            }
        }
    },
    "required": ["products"]
}


@dataclass
class DiscoveryResult:
    """Standardized discovery output from Firecrawl exploration"""
    url: str
    dispensary_name: str
    timestamp: datetime
    products: List[Dict[str, Any]]
    field_map: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    firecrawl_credits_used: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class FirecrawlExplorer:
    """
    Reusable Firecrawl discovery tool for exploring dispensary websites.

    Use this when adding a new scraper to understand the site structure
    before writing Playwright extraction logic.

    Example:
        explorer = FirecrawlExplorer(api_key=settings.firecrawl_api_key)
        result = await explorer.discover(
            url="https://new-dispensary.com/menu",
            name="New Dispensary"
        )
        explorer.save_discovery(result, "discovery_output/")

    Attributes:
        api_key: Firecrawl API key (from .env.mcp)
        base_url: Firecrawl API base URL
    """

    FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1"

    def __init__(self, api_key: str):
        """
        Initialize Firecrawl explorer.

        Args:
            api_key: Firecrawl API key (format: fc-xxx)
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info("Initialized FirecrawlExplorer")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self.session

    async def discover(
        self,
        url: str,
        name: str,
        actions: Optional[List[Dict]] = None,
        wait_for: int = 3000
    ) -> DiscoveryResult:
        """
        Explore a dispensary website using Firecrawl LLM extraction.

        Args:
            url: Menu/products page URL
            name: Human-readable dispensary name
            actions: Optional Firecrawl actions (age gate, scroll, etc.)
            wait_for: Milliseconds to wait for page load (default: 3000)

        Returns:
            DiscoveryResult with products, field_map, and metadata

        Example actions:
            [
                {"type": "click", "selector": "button:has-text('21+')"},
                {"type": "wait", "milliseconds": 2000},
                {"type": "scroll", "direction": "down", "amount": "full"}
            ]
        """
        logger.info(f"Discovering {name} at {url}")

        session = await self._get_session()

        # Build Firecrawl scrape request
        payload = {
            "url": url,
            "formats": ["json"],  # Changed from "extract" to "json"
            "jsonOptions": {  # Changed from "extract" to "jsonOptions"
                "schema": CANNABIS_PRODUCT_SCHEMA,
                "systemPrompt": (
                    "Extract all cannabis products from this dispensary menu page. "
                    "Include all available product information (name, brand, price, "
                    "weight, THC/CBD percentages, stock status, URLs, images, etc.). "
                    "Be comprehensive and extract every product you find."
                )
            },
            "waitFor": wait_for,
            "timeout": 180000  # 3 minutes (Firecrawl default is 30s)
        }

        # Add actions if provided (age gates, scrolling, etc.)
        if actions:
            payload["actions"] = actions

        logger.debug(f"Firecrawl request payload: {json.dumps(payload, indent=2)}")

        try:
            # Call Firecrawl API
            async with session.post(
                f"{self.FIRECRAWL_API_URL}/scrape",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)  # 2 min timeout
            ) as response:
                # Get response body for error debugging
                response_text = await response.text()

                if response.status >= 400:
                    logger.error(f"Firecrawl API error: {response.status}")
                    logger.error(f"Response body: {response_text}")
                    try:
                        error_data = json.loads(response_text)
                        error_msg = error_data.get("error", error_data.get("message", response_text))
                        logger.error(f"Error message: {error_msg}")
                    except:
                        pass

                response.raise_for_status()
                data = json.loads(response_text)

                # Extract products from response
                # Firecrawl returns extracted data in "llm_extraction" field when using jsonOptions
                extraction_data = data.get("llm_extraction", data.get("extract", {}))
                products = extraction_data.get("products", [])

                if not products:
                    logger.warning(f"No products found for {name} at {url}")

                # Calculate credits used (estimate based on response)
                credits_used = self._estimate_credits(data)

                # Generate field map from discovered products
                field_map = self._generate_field_map(products)

                # Build metadata
                metadata = {
                    "product_count": len(products),
                    "fields_found": list(field_map.keys()),
                    "firecrawl_response_success": data.get("success", False),
                    "firecrawl_metadata": data.get("metadata", {})
                }

                return DiscoveryResult(
                    url=url,
                    dispensary_name=name,
                    timestamp=datetime.utcnow(),
                    products=products,
                    field_map=field_map,
                    metadata=metadata,
                    firecrawl_credits_used=credits_used
                )

        except aiohttp.ClientError as e:
            logger.error(f"Firecrawl API error for {name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during discovery for {name}: {e}")
            raise

    def _estimate_credits(self, response_data: Dict[str, Any]) -> int:
        """
        Estimate Firecrawl credits used based on response metadata.

        Firecrawl typically charges 1-5 credits per scrape depending on:
        - Page complexity
        - JavaScript rendering
        - Extraction complexity

        Returns conservative estimate if actual usage not available.
        """
        # Check if Firecrawl provides actual credit usage
        metadata = response_data.get("metadata", {})
        if "creditsUsed" in metadata:
            return metadata["creditsUsed"]

        # Otherwise estimate conservatively
        # Simple page with extraction: ~3-5 credits
        return 5

    def _generate_field_map(
        self,
        products: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze Firecrawl output to identify extraction patterns.

        Returns dict mapping field names to:
        - coverage: percentage of products with this field
        - example: sample value
        - pattern: regex or extraction pattern (if applicable)

        Args:
            products: List of product dictionaries from Firecrawl

        Returns:
            Field map with coverage stats and examples
        """
        if not products:
            return {}

        field_map = {}
        total_products = len(products)

        # Analyze each potential field
        all_fields = set()
        for product in products:
            all_fields.update(product.keys())

        for field_name in all_fields:
            # Count how many products have this field
            present_count = sum(1 for p in products if p.get(field_name) is not None)
            coverage = (present_count / total_products) * 100

            # Get example value
            example_value = next(
                (p.get(field_name) for p in products if p.get(field_name) is not None),
                None
            )

            # Detect patterns for certain fields
            pattern = self._detect_pattern(field_name, products)

            field_map[field_name] = {
                "coverage": round(coverage, 1),
                "present_count": present_count,
                "example": example_value,
                "pattern": pattern
            }

        return field_map

    def _detect_pattern(
        self,
        field_name: str,
        products: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Detect extraction pattern for a field.

        Returns regex pattern or description of how to extract this field.
        """
        # Get sample values for this field
        values = [p.get(field_name) for p in products if p.get(field_name) is not None]
        if not values:
            return None

        # Pattern detection based on field type
        if field_name == "weight":
            # Analyze weight formats
            if any(isinstance(v, str) and 'g' in v.lower() for v in values):
                return r'(\d+\.?\d*)\s*(g|gr|gram)'
            elif any(isinstance(v, str) and 'oz' in v.lower() for v in values):
                return r'(\d+\.?\d*)\s*(oz|ounce)'
            elif any(isinstance(v, str) and 'mg' in v.lower() for v in values):
                return r'(\d+\.?\d*)\s*(mg|milligram)'
            return "Regex: (\\d+\\.?\\d*)\\s*(g|oz|mg)"

        elif field_name in ["thc_percentage", "cbd_percentage"]:
            # Cannabinoid percentage pattern
            return r'(\d+\.?\d*)%?\s*(THC|CBD|thc|cbd)'

        elif field_name == "price":
            # Price pattern
            return r'\$?(\d+\.?\d*)'

        elif field_name == "strain_type":
            # Strain type indicator
            sample_str_types = [str(v).upper() for v in values[:10]]
            if any(t in ['I', 'S', 'H'] for t in sample_str_types):
                return "Single letter: I/S/H"
            return "Full name: Indica/Sativa/Hybrid"

        elif field_name == "in_stock":
            # Stock status
            return "Boolean: true/false or CSS class check"

        # For other fields, just note direct extraction
        return "Direct extraction"

    def save_discovery(
        self,
        result: DiscoveryResult,
        output_dir: str = "discovery_output"
    ):
        """
        Save discovery results to JSON and generate field map markdown.

        Creates:
            - {output_dir}/{name}_discovery.json - Full Firecrawl output
            - {output_dir}/{name}_field_map.md - Human-readable field guide

        Args:
            result: DiscoveryResult from discover()
            output_dir: Directory to save files (default: discovery_output)
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Slugify dispensary name for filenames
        slug = self._slugify(result.dispensary_name)

        # Save full discovery JSON
        json_path = output_path / f"{slug}_discovery.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Saved discovery JSON to {json_path}")

        # Generate and save field map markdown
        field_map_md = self._generate_field_map_markdown(result)
        md_path = output_path / f"{slug}_field_map.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(field_map_md)
        logger.info(f"Saved field map to {md_path}")

        logger.info(
            f"✓ Discovery complete for {result.dispensary_name}: "
            f"{len(result.products)} products, {result.firecrawl_credits_used} credits"
        )

    def _slugify(self, text: str) -> str:
        """Convert text to filename-safe slug"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '_', text)
        return text.strip('_')

    def _generate_field_map_markdown(self, result: DiscoveryResult) -> str:
        """
        Generate markdown field map documentation.

        Returns formatted markdown with:
        - Header with metadata
        - Field coverage table
        - Recommended extraction patterns
        - Edge cases and notes
        """
        md_lines = [
            f"# {result.dispensary_name} Field Map",
            "",
            f"**Discovery Date**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"**Products Found**: {len(result.products)}",
            f"**Firecrawl Credits Used**: {result.firecrawl_credits_used}",
            f"**Source URL**: {result.url}",
            "",
            "## Available Fields",
            "",
            "| Field | Coverage | Present | Example | Extraction Pattern |",
            "|-------|----------|---------|---------|-------------------|"
        ]

        # Sort fields by coverage (highest first)
        sorted_fields = sorted(
            result.field_map.items(),
            key=lambda x: x[1]['coverage'],
            reverse=True
        )

        for field_name, field_info in sorted_fields:
            coverage = field_info['coverage']
            present = field_info['present_count']
            example = field_info['example']
            pattern = field_info.get('pattern', 'Direct extraction')

            # Format example (truncate if too long)
            if isinstance(example, str) and len(example) > 40:
                example = example[:37] + "..."
            example_str = str(example) if example is not None else "N/A"

            md_lines.append(
                f"| {field_name} | {coverage}% | {present}/{len(result.products)} | "
                f"{example_str} | {pattern} |"
            )

        # Add notes section
        md_lines.extend([
            "",
            "## Notes & Recommendations",
            "",
            "### Field Coverage Analysis",
            ""
        ])

        # Identify critical fields with low coverage
        critical_fields = ["name", "price", "weight", "url"]
        low_coverage_critical = [
            (field, result.field_map[field]['coverage'])
            for field in critical_fields
            if field in result.field_map and result.field_map[field]['coverage'] < 95
        ]

        if low_coverage_critical:
            md_lines.append("**⚠️ Critical Fields with Low Coverage:**")
            for field, coverage in low_coverage_critical:
                md_lines.append(f"- `{field}`: {coverage}% (should be >95%)")
            md_lines.append("")
        else:
            md_lines.append("✓ All critical fields have >95% coverage")
            md_lines.append("")

        # High coverage optional fields
        optional_fields = ["image_url", "description", "batch_number", "strain_type"]
        available_optional = [
            (field, result.field_map[field]['coverage'])
            for field in optional_fields
            if field in result.field_map and result.field_map[field]['coverage'] > 50
        ]

        if available_optional:
            md_lines.append("**Bonus Fields Available (>50% coverage):**")
            for field, coverage in available_optional:
                md_lines.append(f"- `{field}`: {coverage}% - Consider adding to scraper")
            md_lines.append("")

        # Edge cases section
        md_lines.extend([
            "### Edge Cases to Handle",
            "",
            "- **Missing data**: Some fields may be null/empty - handle gracefully",
            "- **Inconsistent formats**: Validate and normalize extracted values",
            "- **Stock status**: Check both boolean flag and CSS classes",
            "",
            "## Usage in Playwright Scraper",
            "",
            "Use this field map as reference when implementing extraction logic:",
            "",
            "```python",
            "# Example based on discovered fields:",
            "async def _extract_products(self, page: Page):",
            "    # TODO: Update with actual CSS selectors from Firecrawl HTML",
            "    items = await page.query_selector_all('.product-item')",
            "    for item in items:",
            "        # Extract fields based on patterns above",
            "        name = await item.query_selector('.product-name')",
            "        price = await item.query_selector('.price')",
            "        # ... etc",
            "```",
            "",
            "---",
            "",
            "*Generated by FirecrawlExplorer - Do not edit manually*"
        ])

        return "\n".join(md_lines)

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("Closed FirecrawlExplorer session")
