---
name: market-research
description: Browse a competitor or similar website, analyze it across UX & design, feature inventory, marketing copy, and SEO, then produce a prioritized gap-analysis report tailored to the Utah cannabis price-comparison app. Usage: /market-research <url>
tools: WebFetch, Write, Read
---

# Market Research Skill

Given a competitor or similar website URL, perform a structured analysis and save a tailored gap-analysis report to `dev/research/`.

**Invocation**: `/market-research <url>`

---

## Phase 1: Setup

1. Extract the base domain from the URL (e.g., `leafly.com`) — this becomes the report filename: `dev/research/<domain>-analysis.md`.
2. Note today's date for the report header.
3. Read `.claude/skills/market-research/references/app-context.md` — this contains the current app's feature inventory. You MUST load this before forming any opinions so recommendations are specific and actionable.

---

## Phase 2: Crawl Key Pages

Use WebFetch to retrieve the following pages (infer URLs from navigation links found on the homepage):

| Page | Purpose |
|------|---------|
| Homepage | Hero, value prop, nav structure, CTAs |
| Product listing / search results | Search UX, filters, product cards |
| One product detail page | Product info layout, pricing display, CTAs |
| "How it works" or pricing/about page | Positioning, trust signals |
| About or contact page | Brand story, compliance messaging |

For each page, use this prompt with WebFetch:
> "Extract: page title, meta description, main headline, navigation links, all CTAs (button text + placement), trust/compliance signals, key feature elements visible, URL structure, and any schema markup signals. Be thorough — capture exact wording of headlines and CTAs."

If a page is JavaScript-heavy or returns no useful content, note it in Raw Notes and move on — do not retry the same URL.

---

## Phase 3: Analyze Across 4 Dimensions

Cross-reference what you found in Phase 2 against the app-context.md feature inventory.

### 3a. UX & Design
- Navigation structure and depth (how many clicks to reach products?)
- Search UX: placement, autocomplete signals, filter/sort options, result layout
- Product card design: what data is shown (name, price, weight, THC%, image, dispensary?)
- Mobile responsiveness signals (viewport meta, mobile-friendly layout cues)
- Visual hierarchy and use of whitespace
- Accessibility cues (alt text, ARIA labels in source)
- Any unique UX patterns not present in the app

### 3b. Feature Inventory
List every distinct user-facing feature found. For each feature, note:
- Whether the app already has it (✅ / ❌ / 🔶 partial)
- If missing, whether it's worth building (your assessment)

### 3c. Marketing & Copy
- Hero headline: exact wording + clarity of value proposition
- Sub-headline or supporting copy
- CTA text and placement above the fold
- Trust signals: reviews, user counts, badges, press mentions
- Compliance/legal messaging: how do they handle cannabis legal disclaimers?
- Tone: clinical, friendly, community-driven, transactional?
- Email capture / newsletter: present?
- Social proof: testimonials, ratings, user-generated content?

### 3d. SEO & Discoverability
- URL slug patterns (e.g., `/strains/blue-dream` vs `/products/123`)
- `<title>` tag quality: descriptive, keyword-rich?
- Meta description presence and quality
- Schema markup signals (JSON-LD, Product schema, BreadcrumbList, etc.)
- Content depth per page: thin vs. rich editorial content?
- Internal linking patterns
- Blog or editorial content section?
- Page load signals (image lazy loading, CDN use, script defer)

---

## Phase 4: Prioritized Recommendations

Produce a ranked list of recommendations for the app. Assign each a priority:

- `🔴 High` — directly impacts patient conversion, retention, or core workflow
- `🟡 Medium` — meaningful UX or marketing improvement
- `🟢 Low` — polish, nice-to-have, or long-term consideration

Format each recommendation as:
```
### [Priority] [Short title]
**Observed on**: [competitor site]
**What they do**: [1-2 sentences]
**Recommended action**: [Specific, actionable change for the app]
```

---

## Phase 5: Write Report

Write the full report to `dev/research/<domain>-analysis.md`. Create the directory if it doesn't exist. Use this structure exactly:

```markdown
# Competitor Analysis: <domain>
**Date**: <today's date>
**Source URL**: <url>
**Analyzed by**: /market-research skill

---

## Executive Summary

(3–5 bullet points capturing the most important findings)

---

## UX & Design Analysis

...

---

## Feature Inventory & Gaps

| Feature | Competitor Has | App Has | Priority to Build |
|---------|---------------|---------|------------------|
| ...     | ✅            | ❌      | 🔴 High          |

...

---

## Marketing & Copy Analysis

...

---

## SEO & Discoverability Signals

...

---

## Prioritized Recommendations for CannabisCompare

(numbered, highest priority first)

---

## Raw Notes

(Anything that didn't fit above — inaccessible pages, unusual observations, direct quotes from the site)
```

---

## Phase 6: Print Summary

After saving the file, output a short terminal summary (max 10 lines):

```
Market Research Complete
━━━━━━━━━━━━━━━━━━━━━━
Site analyzed: <url>
Report saved:  dev/research/<domain>-analysis.md

Top 3 findings:
  🔴 <finding 1>
  🔴 <finding 2>
  🟡 <finding 3>
```

---

## Handling Edge Cases

- **JS-heavy SPA** (blank content returned): Note in Raw Notes; analyze only what was returned (title, meta tags still visible in source).
- **Paywalled pages**: Skip and note; analyze publicly accessible pages only.
- **404 / redirect errors**: Try the root domain; if still failing, note and skip.
- **No cannabis industry context**: Always filter recommendations through the lens of Utah Medical Cannabis patients — features irrelevant to that audience should be deprioritized.
