"""
CLI tool for discovering dispensary website structure using Playwright + LLM.

This script uses Playwright to navigate dispensary pages and capture screenshots/HTML,
then uses LLM vision models to analyze the structure and generate field maps.

Usage:
    python scripts/discover_dispensary.py \
        --url https://new-dispensary.com/menu \
        --name "New Dispensary" \
        --llm gemini \
        --age-gate ".age-confirm-button"

Options:
    --url: Dispensary menu/products page URL (required)
    --name: Human-readable name (required)
    --llm: LLM provider to use - glm, codex, gemini, or claude (default: gemini)
    --age-gate: CSS selector for age gate button (optional)
    --scroll: Enable infinite scroll (optional, default: false)
    --wait-for: CSS selector to wait for (default: .product)
    --output: Output directory (optional, default: discovery_output/)

LLM Options:
    --llm glm       Use GLM (user has subscription) - $0.01 per analysis
    --llm codex     Use OpenAI Codex/GPT-4V (user has subscription) - $0.05 per analysis
    --llm gemini    Use Google Gemini Free (default) - $0.00 per analysis
    --llm claude    Use Claude API (fallback) - $0.10 per analysis

Examples:
    # WholesomeCo with Gemini (free)
    python scripts/discover_dispensary.py \
        --url https://www.wholesome.co/shop \
        --name "WholesomeCo" \
        --llm gemini \
        --age-gate "button:contains('21 or older')" \
        --scroll

    # Curaleaf with GLM (production)
    python scripts/discover_dispensary.py \
        --url https://ut.curaleaf.com/stores/curaleaf-ut-lehi \
        --name "Curaleaf Lehi" \
        --llm glm \
        --age-gate "button:contains('over 18')"
"""

import argparse
import asyncio
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

# Add backend to path so we can import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env.mcp (for LLM API keys)
env_mcp_path = backend_dir.parent / ".env.mcp"
if env_mcp_path.exists():
    load_dotenv(env_mcp_path)

from services.discovery.playwright_explorer import PlaywrightDiscoveryExplorer
from services.discovery.llm_providers import (
    GeminiProvider,
    GLMProvider,
    CodexProvider,
    ClaudeProvider
)


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Discover dispensary structure with Playwright + LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--url",
        required=True,
        help="Dispensary menu/products page URL"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Human-readable dispensary name"
    )
    parser.add_argument(
        "--llm",
        choices=["glm", "codex", "gemini", "claude"],
        default="gemini",
        help="LLM provider to use (default: gemini - free tier)"
    )
    parser.add_argument(
        "--age-gate",
        default=None,
        help="CSS selector for age gate button to click"
    )
    parser.add_argument(
        "--scroll",
        action="store_true",
        help="Enable infinite scroll to load all products"
    )
    parser.add_argument(
        "--wait-for",
        default=".product",
        help="CSS selector to wait for (default: .product)"
    )
    parser.add_argument(
        "--output",
        default="discovery_output",
        help="Output directory for discovery files (default: discovery_output/)"
    )

    args = parser.parse_args()

    # Get LLM provider API key from environment
    if args.llm == "glm":
        api_key = os.getenv("GLM_API_KEY")
        provider_name = "GLM"
        provider = GLMProvider(api_key) if api_key else None
    elif args.llm == "codex":
        api_key = os.getenv("OPENAI_API_KEY")
        provider_name = "OpenAI Codex"
        provider = CodexProvider(api_key) if api_key else None
    elif args.llm == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        provider_name = "Google Gemini"
        provider = GeminiProvider(api_key) if api_key else None
    else:  # claude
        api_key = os.getenv("ANTHROPIC_API_KEY")
        provider_name = "Claude API"
        provider = ClaudeProvider(api_key) if api_key else None

    if not api_key:
        print(f"[ERROR] {provider_name} API key not found in environment")
        print(f"Set {args.llm.upper()}_API_KEY in your .env.mcp file or environment variables")
        print(f"\nExample for .env.mcp:")
        if args.llm == "glm":
            print("GLM_API_KEY=your-glm-api-key-here")
        elif args.llm == "codex":
            print("OPENAI_API_KEY=sk-your-openai-key-here")
        elif args.llm == "gemini":
            print("GEMINI_API_KEY=your-gemini-api-key-here")
        else:
            print("ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here")
        return 1

    # Run discovery
    print(f"\n[INFO] Discovering {args.name}...")
    print(f"   URL: {args.url}")
    print(f"   LLM Provider: {provider_name}")
    print(f"   Estimated Cost: ${provider.get_cost_estimate():.2f}")
    print("")

    explorer = PlaywrightDiscoveryExplorer(headless=True)

    try:
        result = await explorer.discover(
            url=args.url,
            name=args.name,
            llm_provider=provider,
            age_gate_selector=args.age_gate,
            wait_for_selector=args.wait_for,
            scroll_to_load=args.scroll
        )

        # Save results
        explorer.save_discovery(result, args.output)

        # Print summary
        print("\n" + "=" * 60)
        print(f"[SUCCESS] Discovery complete for {args.name}")
        print("=" * 60)
        print(f"  LLM Provider: {result.llm_provider}")
        print(f"  Analysis Cost: ${result.analysis_cost:.2f}")
        print(f"  CSS Selectors Found: {len(result.css_selectors)}")
        print(f"  Field Patterns Found: {len(result.extraction_patterns)}")
        print(f"  Edge Cases Noted: {len(result.edge_cases)}")
        print("")
        print("Output files:")
        slug = explorer._slugify(args.name)
        print(f"  - {result.screenshot_path}")
        print(f"  - {result.html_path}")
        print(f"  - {args.output}/{slug}_discovery.json (full data)")
        print(f"  - {args.output}/{slug}_field_map.md (field guide)")
        print("")

        # Show field coverage summary
        if result.field_map:
            print("Field Map Summary:")
            for field, details in list(result.field_map.items())[:10]:  # Show first 10
                coverage = details.get('coverage', 'N/A')
                selector = details.get('selector', 'N/A')
                print(f"  - {field}: {coverage}% coverage (selector: {selector})")
            if len(result.field_map) > 10:
                print(f"  ... and {len(result.field_map) - 10} more fields")
            print("")

        print("Next steps:")
        print(f"  1. Review field map: cat {args.output}/{slug}_field_map.md")
        print("  2. Use insights to update Playwright scraper")
        print("  3. Test improved scraper via admin dashboard")

        return 0

    except Exception as e:
        print(f"\n[ERROR] Discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Windows Python 3.13 fix for asyncio
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except RuntimeError:
            pass

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
