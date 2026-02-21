"""
Product name cleaning utility.

Removes common junk text that leaks from HTML-composed product names:
- "Add [X] to cart" / "Add to cart" patterns
- Repeated mg tokens ("mg mg mg", "Fruit of mg mg")
- Stray price values ($12.34)
- HTML entities (&amp;, &nbsp;, etc.)

Used by scorer.py before storing original_name on ScraperFlag,
and by scraper_runner.py before passing to ConfidenceScorer.
"""
import re
import html
import logging

logger = logging.getLogger(__name__)

# Ordered list of (pattern, replacement) tuples.
# Applied sequentially so earlier removals can expose later patterns.
_CLEANING_RULES: list[tuple[str, str]] = [
    # "Add 800mg to cart", "Add to cart", "Add 1g to cart"
    (r'[Aa]dd\s+\d*\.?\d*\s*(?:mg|g|oz|ml)?\s*to\s+cart', ''),

    # Repeated "mg" tokens: "mg mg mg", "300mg mg mg", "Fruit of mg mg"
    # This also catches "of mg mg" artifacts from edible product descriptions
    (r'(?:\b\d*\.?\d*\s*mg\s*){2,}', ''),
    (r'\bof\s+(?:mg\s*)+', ' '),

    # Stray price values like "$94.50" or "$135.00"
    (r'\$\d+\.?\d*', ''),

    # Percentage discount values like "30% off", "20% OFF"
    (r'\d+\s*%\s*[Oo][Ff][Ff]', ''),

    # "BUY (4) SELECT..." style promo text
    (r'BUY\s*\(\d+\)[^+]*', ''),

    # "Add" left alone at end of string (artifact after cart text removal)
    (r'\bAdd\s*$', ''),

    # HTML entities
    # (handled via html.unescape below, but catch common ones first)
    (r'&amp;', '&'),
    (r'&nbsp;', ' '),
    (r'&lt;', '<'),
    (r'&gt;', '>'),
]

# After all removals, collapse any runs of whitespace and strip
_COLLAPSE_SPACES = re.compile(r'\s{2,}')


def clean_product_name(name: str) -> str:
    """
    Remove cart text, repeated mg tokens, price values and HTML artifacts
    from a scraped product name.

    Args:
        name: Raw product name string from scraper

    Returns:
        Cleaned product name. Never returns an empty string — if everything
        is stripped, returns the original name unchanged (to avoid data loss).
    """
    if not name:
        return name

    # First pass: unescape HTML entities
    cleaned = html.unescape(name)

    # Apply all regex cleaning rules
    for pattern, replacement in _CLEANING_RULES:
        cleaned = re.sub(pattern, replacement, cleaned)

    # Collapse multiple spaces and trim
    cleaned = _COLLAPSE_SPACES.sub(' ', cleaned).strip()

    if not cleaned:
        # Paranoia: if everything was removed, return original
        logger.warning(f"Name cleaning removed entire string, keeping original: '{name}'")
        return name.strip()

    if cleaned != name.strip():
        logger.debug(f"Name cleaned: '{name}' -> '{cleaned}'")

    return cleaned
