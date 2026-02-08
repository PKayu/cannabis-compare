"""
Weight/quantity parsing utility for cannabis products.

Converts raw weight strings to normalized labels and gram values.
"""
import re
from typing import Tuple, Optional


# Conversion factors to grams
_UNIT_TO_GRAMS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "oz": 28.0,
    "ounce": 28.0,
    "ounces": 28.0,
    "mg": 0.001,
    "milligram": 0.001,
    "milligrams": 0.001,
    "lb": 453.592,
    "lbs": 453.592,
}

# Common fractional ounce names
_FRACTION_NAMES = {
    "eighth": 3.5,
    "quarter": 7.0,
    "half": 14.0,
}

# Regex for numeric value + unit  (e.g., "3.5g", "1 oz", "100mg")
_NUMERIC_UNIT_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*'          # number (integer or decimal)
    r'(g|gram|grams|oz|ounce|ounces|mg|milligram|milligrams|lb|lbs)\b',
    re.IGNORECASE
)

# Regex for fractional ounces  (e.g., "1/8 oz", "1/4oz")
_FRACTION_UNIT_PATTERN = re.compile(
    r'(\d+)\s*/\s*(\d+)\s*'        # fraction like 1/8
    r'(oz|ounce|ounces)\b',
    re.IGNORECASE
)

# Regex for named fractions  (e.g., "an eighth", "quarter ounce")
_NAMED_FRACTION_PATTERN = re.compile(
    r'\b(eighth|quarter|half)\b',
    re.IGNORECASE
)


def parse_weight(raw: Optional[str]) -> Tuple[Optional[str], Optional[float]]:
    """
    Parse a weight string to a normalized label and gram value.

    Args:
        raw: Raw weight string, e.g., "3.5g", "1 oz", "1/8 oz", "100mg"

    Returns:
        Tuple of (normalized_label, grams):
          - ("3.5g", 3.5)
          - ("1oz", 28.0)
          - ("3.5g", 3.5)  for "1/8 oz"
          - ("100mg", 0.1)
          - (None, None) if unparseable or None input
    """
    if not raw or not raw.strip():
        return None, None

    text = raw.strip()

    # Try fractional ounces first (e.g., "1/8 oz")
    match = _FRACTION_UNIT_PATTERN.search(text)
    if match:
        numerator = float(match.group(1))
        denominator = float(match.group(2))
        if denominator != 0:
            oz_value = numerator / denominator
            grams = oz_value * 28.0
            return _format_grams(grams), round(grams, 3)

    # Try named fractions (e.g., "eighth", "quarter")
    match = _NAMED_FRACTION_PATTERN.search(text)
    if match:
        name = match.group(1).lower()
        grams = _FRACTION_NAMES[name]
        return _format_grams(grams), grams

    # Try numeric + unit (e.g., "3.5g", "1 oz", "100mg")
    match = _NUMERIC_UNIT_PATTERN.search(text)
    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()
        multiplier = _UNIT_TO_GRAMS.get(unit, 1.0)
        grams = value * multiplier
        return _format_label(value, unit), round(grams, 3)

    return None, None


def extract_weight_from_name(product_name: str) -> Tuple[str, Optional[str], Optional[float]]:
    """
    Extract weight from a product name and return the cleaned name.

    Args:
        product_name: Full product name, e.g., "Blue Dream 3.5g"

    Returns:
        Tuple of (clean_name, weight_label, weight_grams):
          - ("Blue Dream", "3.5g", 3.5)
          - ("Blue Dream", None, None) if no weight found
    """
    if not product_name:
        return product_name, None, None

    # Try to find and strip weight in parentheses (e.g., "Blue Dream (3.5g)")
    paren_weight = re.compile(
        r'\s*\((\d+(?:\.\d+)?\s*(?:g|gram|grams|oz|ounce|mg|milligram|milligrams|ml))\)\s*$',
        re.IGNORECASE
    )

    match = paren_weight.search(product_name)
    if match:
        weight_str = match.group(1)
        clean_name = product_name[:match.start()].strip()
        label, grams = parse_weight(weight_str)
        if label and clean_name:
            return clean_name, label, grams

    # Try to find and strip weight from end of name
    # Pattern: name followed by weight at the end
    weight_suffix = re.compile(
        r'\s+'                              # whitespace separator
        r'(\d+(?:\.\d+)?\s*'               # number
        r'(?:g|gram|grams|oz|ounce|mg|milligram|milligrams))\s*$',  # unit at end
        re.IGNORECASE
    )

    match = weight_suffix.search(product_name)
    if match:
        weight_str = match.group(1)
        clean_name = product_name[:match.start()].strip()
        label, grams = parse_weight(weight_str)
        if label and clean_name:
            return clean_name, label, grams

    # Try fractional ounce suffix  (e.g., "Blue Dream 1/8 oz")
    fraction_suffix = re.compile(
        r'\s+(\d+\s*/\s*\d+\s*(?:oz|ounce))\s*$',
        re.IGNORECASE
    )

    match = fraction_suffix.search(product_name)
    if match:
        weight_str = match.group(1)
        clean_name = product_name[:match.start()].strip()
        label, grams = parse_weight(weight_str)
        if label and clean_name:
            return clean_name, label, grams

    return product_name, None, None


def _format_label(value: float, unit: str) -> str:
    """Format a clean label like '3.5g', '1oz', '100mg'."""
    unit_lower = unit.lower()

    # Normalize unit names to short form
    if unit_lower in ("gram", "grams"):
        short_unit = "g"
    elif unit_lower in ("ounce", "ounces"):
        short_unit = "oz"
    elif unit_lower in ("milligram", "milligrams"):
        short_unit = "mg"
    elif unit_lower in ("lb", "lbs"):
        short_unit = "lb"
    else:
        short_unit = unit_lower

    # Format number: drop trailing .0
    if value == int(value):
        return f"{int(value)}{short_unit}"
    return f"{value}{short_unit}"


def _format_grams(grams: float) -> str:
    """Format a gram value into the most natural label."""
    # Common cannabis sizes mapped to conventional labels
    common_sizes = {
        0.5: "0.5g",
        1.0: "1g",
        2.0: "2g",
        3.5: "3.5g",
        7.0: "7g",
        14.0: "14g",
        28.0: "1oz",
    }

    rounded = round(grams, 1)
    if rounded in common_sizes:
        return common_sizes[rounded]

    # Fall back to grams
    if grams == int(grams):
        return f"{int(grams)}g"
    return f"{grams}g"
