"""
Playwright-based discovery explorer for dispensary websites.

Uses Playwright to navigate sites, dismiss age gates, and capture
screenshots/HTML for LLM analysis.
"""

from playwright.async_api import async_playwright, Page
from typing import Optional
from pathlib import Path
from datetime import datetime
import re
import json

from services.discovery.models import DiscoveryResult
from services.discovery.llm_providers import LLMProvider


class PlaywrightDiscoveryExplorer:
    """
    Uses Playwright to capture screenshots and HTML from dispensary pages.

    Handles age gates using existing scraper patterns, then captures content
    for LLM analysis.

    Example:
        explorer = PlaywrightDiscoveryExplorer()
        result = await explorer.discover(
            url="https://dispensary.com/menu",
            name="Dispensary Name",
            age_gate_selector=".age-gate-button",
            llm_provider=GeminiProvider(api_key="...")
        )
        explorer.save_discovery(result, "discovery_output")
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    async def discover(
        self,
        url: str,
        name: str,
        llm_provider: LLMProvider,
        age_gate_selector: Optional[str] = None,
        wait_for_selector: str = ".product",  # Wait for products to load
        scroll_to_load: bool = False
    ) -> DiscoveryResult:
        """
        Discover dispensary structure using Playwright + LLM analysis.

        Args:
            url: Dispensary menu URL
            name: Human-readable name
            llm_provider: LLM provider instance (GLM, Codex, Gemini, Claude)
            age_gate_selector: CSS selector for age gate dismiss button
            wait_for_selector: Selector to wait for (indicates page loaded)
            scroll_to_load: Whether to scroll to trigger lazy-loaded products

        Returns:
            DiscoveryResult with field maps and analysis
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            try:
                # Navigate to page
                print(f"[INFO] Navigating to {url}")
                await page.goto(url, wait_until="domcontentloaded")

                # Handle age gate if present
                if age_gate_selector:
                    print(f"[INFO] Dismissing age gate with selector: {age_gate_selector}")
                    await self._dismiss_age_gate(page, age_gate_selector)

                # Wait for products to load
                print(f"[INFO] Waiting for products (selector: {wait_for_selector})")
                try:
                    await page.wait_for_selector(wait_for_selector, timeout=10000)
                except Exception as e:
                    print(f"[WARNING] Timeout waiting for {wait_for_selector}: {e}")

                # Scroll if needed
                if scroll_to_load:
                    print("[INFO] Scrolling to load all products")
                    await self._scroll_to_load_all(page)

                # Capture screenshot and HTML
                screenshot_path = f"discovery_output/screenshots/{self._slugify(name)}.png"
                Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)

                print(f"[INFO] Capturing screenshot: {screenshot_path}")
                await page.screenshot(path=screenshot_path, full_page=True)
                html_content = await page.content()

                # Save HTML for reference
                html_path = f"discovery_output/html/{self._slugify(name)}.html"
                Path(html_path).parent.mkdir(parents=True, exist_ok=True)
                Path(html_path).write_text(html_content, encoding='utf-8')
                print(f"[INFO] Saved HTML: {html_path}")

                # Analyze with LLM
                print(f"[INFO] Analyzing with {llm_provider.__class__.__name__}")
                llm_result = await llm_provider.analyze_screenshot(
                    screenshot_path=screenshot_path,
                    html_content=html_content,
                    prompt=self._get_analysis_prompt()
                )

                # Create discovery result
                return DiscoveryResult(
                    url=url,
                    dispensary_name=name,
                    timestamp=datetime.utcnow(),
                    screenshot_path=screenshot_path,
                    html_path=html_path,
                    field_map=llm_result.field_map,
                    css_selectors=llm_result.css_selectors,
                    extraction_patterns=llm_result.extraction_patterns,
                    edge_cases=llm_result.edge_cases,
                    llm_provider=llm_provider.__class__.__name__,
                    analysis_cost=llm_provider.get_cost_estimate()
                )

            finally:
                await browser.close()

    async def _dismiss_age_gate(self, page: Page, selector: str):
        """Dismiss age gate using CSS selector."""
        try:
            button = await page.wait_for_selector(selector, timeout=5000)
            if button:
                await button.click()
                await page.wait_for_timeout(2000)  # Wait for modal to close
                print("[INFO] Age gate dismissed successfully")
        except Exception as e:
            print(f"[WARNING] Age gate dismissal failed or not present: {e}")

    async def _scroll_to_load_all(self, page: Page, max_scrolls: int = 50):
        """Scroll to bottom repeatedly to load all products."""
        previous_count = 0
        stable_count = 0

        for i in range(max_scrolls):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

            # Count products
            try:
                current_count = await page.locator(".product").count()
            except:
                current_count = 0

            if current_count == previous_count:
                stable_count += 1
                if stable_count >= 3:  # Stable for 3 iterations
                    print(f"[INFO] Scroll complete ({current_count} products visible)")
                    break
            else:
                stable_count = 0
                print(f"[INFO] Scroll iteration {i+1}: {current_count} products visible")

            previous_count = current_count

    def _get_analysis_prompt(self) -> str:
        """Get the prompt for LLM analysis."""
        return """
Analyze this cannabis dispensary menu page and extract the product structure.

**CRITICAL INSTRUCTIONS**:
- You MUST use ACTUAL CSS class names from the provided HTML context
- DO NOT invent or guess class names - extract them directly from the HTML
- If HTML context is provided, use it as the PRIMARY source for selectors
- The screenshot is for visual reference only - selectors must match the HTML

For each visible product, identify:

1. **CSS Selectors** (extract from HTML, do not invent):
   - Product container selector (e.g., .productListItem, .product-card)
   - Name/title selector (e.g., .product-name, h3.title)
   - Price selector (e.g., .price, .product-price)
   - Brand selector if visible (e.g., .brand, .manufacturer)
   - Weight/size selector if separate element exists
   - THC/CBD percentage selectors if separate elements exist
   - Stock status indicator if present
   - Product URL/link selector
   - Product image selector

2. **Extraction Patterns** (regex for text extraction):
   - How to parse weight if embedded in product name or description
   - How to extract THC/CBD percentages from text
   - How to determine stock status (CSS class? text pattern?)
   - Price format and currency extraction

3. **Field Coverage**:
   - What percentage of products have each field?
   - Which fields are consistently present (100%) vs optional (<100%)?

4. **Edge Cases**:
   - Products without explicit weight elements (extract from name/description)
   - Out-of-stock products and how they're indicated
   - Missing brand information
   - Special formatting or data quirks

**HTML Context Analysis**:
1. Examine the provided HTML carefully
2. Find repeating product elements (container selector)
3. Within each container, find child elements for each field
4. Extract the EXACT class names, IDs, or attribute selectors
5. Verify your selectors would match multiple products, not just one

Analyze the HTML structure first, then use the screenshot for visual confirmation.
"""

    def _slugify(self, text: str) -> str:
        """Convert text to filename-safe slug."""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '_', text)
        return text.strip('_')

    def save_discovery(self, result: DiscoveryResult, output_dir: str = "discovery_output"):
        """
        Save discovery results to JSON and generate field map markdown.

        Creates:
            - {output_dir}/{name}_discovery.json - Full discovery data
            - {output_dir}/{name}_field_map.md - Human-readable field guide
        """
        slug = self._slugify(result.dispensary_name)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save JSON
        json_path = output_path / f"{slug}_discovery.json"
        json_data = {
            "url": result.url,
            "dispensary_name": result.dispensary_name,
            "timestamp": result.timestamp.isoformat(),
            "screenshot_path": result.screenshot_path,
            "html_path": result.html_path,
            "field_map": result.field_map,
            "css_selectors": result.css_selectors,
            "extraction_patterns": result.extraction_patterns,
            "edge_cases": result.edge_cases,
            "llm_provider": result.llm_provider,
            "analysis_cost": result.analysis_cost
        }
        json_path.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
        print(f"[INFO] Saved discovery JSON: {json_path}")

        # Generate markdown field map
        md_path = output_path / f"{slug}_field_map.md"
        markdown = self._generate_field_map_markdown(result)
        md_path.write_text(markdown, encoding='utf-8')
        print(f"[INFO] Saved field map: {md_path}")

    def _generate_field_map_markdown(self, result: DiscoveryResult) -> str:
        """Generate human-readable markdown field map."""
        md = f"# {result.dispensary_name} Field Map\n\n"
        md += f"**Discovery Date**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += f"**URL**: {result.url}\n"
        md += f"**LLM Provider**: {result.llm_provider}\n"
        md += f"**Analysis Cost**: ${result.analysis_cost:.2f}\n\n"

        # CSS Selectors
        md += "## CSS Selectors\n\n"
        if result.css_selectors:
            for field, selector in result.css_selectors.items():
                md += f"- **{field}**: `{selector}`\n"
        else:
            md += "*No CSS selectors identified*\n"
        md += "\n"

        # Extraction Patterns
        md += "## Extraction Patterns\n\n"
        if result.extraction_patterns:
            for field, pattern in result.extraction_patterns.items():
                md += f"- **{field}**: `{pattern}`\n"
        else:
            md += "*No extraction patterns identified*\n"
        md += "\n"

        # Field Map Details
        md += "## Field Map\n\n"
        if result.field_map:
            md += "| Field | Selector | Pattern | Coverage |\n"
            md += "|-------|----------|---------|----------|\n"
            for field, details in result.field_map.items():
                selector = details.get('selector', 'N/A')
                pattern = details.get('pattern', 'N/A')
                coverage = details.get('coverage', 'N/A')
                md += f"| {field} | `{selector}` | `{pattern}` | {coverage}% |\n"
        else:
            md += "*No field map data available*\n"
        md += "\n"

        # Edge Cases
        md += "## Edge Cases\n\n"
        if result.edge_cases:
            for case in result.edge_cases:
                md += f"- {case}\n"
        else:
            md += "*No edge cases noted*\n"
        md += "\n"

        # Product Structure
        md += "## Product Structure\n\n"
        md += "```\n"
        md += result.product_structure if hasattr(result, 'product_structure') else "N/A"
        md += "\n```\n\n"

        # Next Steps
        md += "## Next Steps\n\n"
        md += "1. Review field map and CSS selectors\n"
        md += "2. Update Playwright scraper with discovered selectors\n"
        md += "3. Test scraper via admin dashboard\n"
        md += "4. Validate field extraction rates\n"

        return md
