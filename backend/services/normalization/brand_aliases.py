"""
Canonical brand alias map for Utah medical cannabis brands.

Keys and values are NORMALIZED brand names — i.e. what
ProductMatcher.normalize_brand_name() produces BEFORE the alias lookup:
lowercase, corporate suffixes (inc/llc/co/corp/company/ltd) stripped at word
boundaries, punctuation removed, whitespace collapsed.

To add an alias: run the variant through normalize_brand_name() mentally
(lowercase, no punctuation) and map it to the canonical normalized form.
Keep this map in sync with real Brand rows — audit with:
    SELECT name, normalized_name FROM brands ORDER BY normalized_name;
"""

BRAND_ALIASES: dict[str, str] = {
    # WholesomeCo (vertically integrated; appears with and without space)
    "wholesome": "wholesomeco",
    "wholesome co": "wholesomeco",
    "wholesomeco cannabis": "wholesomeco",
    # Dragonfly Wellness
    "dragonfly": "dragonfly wellness",
    # Beehive Farmacy / Beehive brand listings
    "beehive farmacy": "beehive",
    "beehives own": "beehive",
    # Zion Cultivars / Zion Alchemy
    "zion cultivars": "zion",
    "zion alchemy": "zion",
    # Tryke / Reef house brand
    "tryke companies": "tryke",
    # Standard Wellness Utah
    "standard wellness utah": "standard wellness",
    # Pure Plan / PurePlan
    "pure plan": "pureplan",
    # Riverside Farm(s)
    "riverside farms": "riverside farm",
    # High Variety (Curaleaf Utah house brand appears both ways)
    "hi variety": "high variety",
    # Boojum Group
    "boojum group": "boojum",
    # Sugar House / Sugarhouse
    "sugar house": "sugarhouse",
}
