# The Secret Greenhouse - Design System Documentation

## Concept Overview

**Theme Name:** The Secret Greenhouse
**Core Concept:** A hidden greenhouse sanctuary in the Utah mountains where passionate cultivators grow something special. Users gain access to this private, earthy space to discover what's being cultivated.

**Primary Emotion:** Warmth, sanctuary, hidden discovery, insider knowledge
**Tone:** Cultivator-to-cultivator, earthy, welcoming, exclusive but accessible

---

## Visual Language

### Color Palette

#### Primary Colors
- **Deep Forest Green** `#1a3c28` - Backgrounds, navigation, rich natural feel
- **Medium Foliage Green** `#2d5a3d` - Cards, secondary backgrounds
- **Warm Wood Brown** `#8b6f47` - Text, accents, natural warmth
- **Golden Amber** `#f4a460` - CTAs, highlights, sunlight effects

#### Secondary Colors
- **Rich Soil Brown** `#3d2914` - Dark backgrounds, contrast
- **Light Wood Tone** `#d4a574` - Secondary accents, borders
- **Soft Glass White** `#f5f5f0` - Text on dark backgrounds, glass reflections

#### Accent Colors
- **Grow Light Green** `#4ade80` - In-stock indicators, success states
- **Warm Sunlight** `#fbbf24` - Warnings, price highlights
- **Condensation Blue** (subtle) `#e0f2fe` - Glass effects, cool accents

### Typography

#### Headlines
- **Primary:** `Playfair Display` or `Crimson Pro` (elegant serif)
- **Secondary:** `Cormorant Garamond` (handcrafted feel)
- **Usage:** Page titles, section headers, product names

#### Body Text
- **Primary:** `Inter` or `Source Sans Pro` (clean, readable)
- **Secondary:** `Lato` (warm but professional)
- **Usage:** Product descriptions, reviews, general content

#### Handwritten/Accent
- **Primary:** `Caveat` or `Patrick Hand` (cultivator tags, labels)
- **Usage:** Price tags, handwritten notes, cultivator signatures

#### Type Scale
```
H1: 3rem / 48px (Landing hero title)
H2: 2.25rem / 36px (Page headers)
H3: 1.75rem / 28px (Section headers, product names)
H4: 1.25rem / 20px (Card titles, labels)
Body: 1rem / 16px (Standard text)
Small: 0.875rem / 14px (Meta info, captions)
```

### Textures & Effects

#### Primary Textures
- **Glass condensation:** Subtle water droplet overlay with blur
- **Wood grain:** Faint natural wood patterns on backgrounds
- **Leaf patterns:** Monstera or cannabis leaf silhouettes (subtle opacity)
- **Water droplets:** Scattered, varying sizes, subtle shadows
- **Organic shapes:** Irregular borders, non-rectangular cards

#### Lighting Effects
- **Dappled sunlight:** Warm light rays through glass
- **Grow light glow:** Warm amber radiance on active elements
- **Vignette:** Soft dark edges, warm center focus
- **Backlighting:** Subtle glow behind glass/elements

---

## UI Components

### Navigation

**Design:**
- Background: Deep forest green (`#1a3c28`)
- Menu items: Wooden plaque style with subtle texture
- Active state: Warm amber glow (`#f4a460`), illuminated
- Hover: Leaf/vine growth animation, subtle brightness increase
- Mobile: Slide-out drawer with condensation effect

**Elements:**
```
[🌿 Home] [🌿 Products] [🌿 Dispensaries] [🌿 Profile]
```

### Buttons & CTAs

**Primary Button (Sunlit):**
- Background: Linear gradient (golden amber to warm orange)
- Text: Deep forest green (high contrast)
- Shadow: Soft warm glow
- Hover: Brightness increase, subtle growth animation
- Shape: Slightly rounded corners (organic feel)

**Secondary Button (Wood Tag):**
- Background: Wood brown with texture
- Border: Subtle wood grain edge
- Text: Warm white
- Hover: Slight lift, warmer glow

### Product Cards

**Layout:**
```
┌─────────────────────────────────────┐
│  [Glass texture background]         │
│                                     │
│     ┌─────────────────┐             │
│     │                 │   🏷️ Tag   │
│     │   Product Image │   $45.00    │
│     │   (on branch)   │   [In Stock]│
│     │                 │   🌿 Glow   │
│     └─────────────────┘             │
│                                     │
│  "Northern Lights"                  │
│  ───────────────────                │
│  THC: 22% | CBD: 1%                 │
│  Indica • Earthy • Pine             │
│                                     │
│  [🌿 Add to Watchlist]              │
└─────────────────────────────────────┘
```

**Animations:**
- **Idle:** Subtle plant sway (gentle rotation)
- **Hover:** Card lifts with shadow, leaves shift, warm glow intensifies
- **Add to watchlist:** Ribbon wraps around plant or tag ties to branch

### Search & Filters

**Search Bar:**
- Placeholder: "What's growing today?"
- Style: Glass effect with condensation drops
- Focus: Warm amber glow, slight brightness
- Icon: Magnifying glass with leaf accent

**Filters:**
- Displayed as "garden categories"
- Style: Wooden tags or seed packet labels
- Active: Grow light glow effect
- Categories: Indica/Sativa/Hybrid, Potency, Harvest Time

### Dispensary Cards

**Layout:**
```
┌─────────────────────────────────────┐
│  🌿 Wholesome Co.                   │
│  Cultivation Partner                │
│  ──────────────────────             │
│                                     │
│  [Greenhouse illustration]          │
│                                     │
│  "Salt Lake City's hidden garden"   │
│                                     │
│  📍 Salt Lake City, UT              │
│  🌱 24 strains growing              │
│                                     │
│  [Explore Garden →]                │
└─────────────────────────────────────┘
```

### Review Cards

**Layout:**
```
┌─────────────────────────────────────┐
│  👤 LocalGrower_U       🌿 Expert   │
│  Master Cultivator                  │
│  ──────────────────────             │
│                                     │
│  "Helped with my chronic pain..."   │
│                                     │
│  ⭐⭐⭐⭐⭐  (5.0)                   │
│                                     │
│  Medical: Pain relief, Sleep        │
│  Wellness: Relaxation               │
│                                     │
│  🕐 Posted 3 days ago               │
└─────────────────────────────────────┘
```

---

## Page Layouts

### Landing Page (Hero)

**Structure:**
```
┌─────────────────────────────────────────────────┐
│  [Navigation: Deep green, wooden plaques]      │
├─────────────────────────────────────────────────┤
│                                                 │
│            [Condensation on glass]              │
│                                                 │
│         Utah's Best-Kept Garden                 │
│                                                 │
│    Discover what local cultivators are         │
│    growing behind the glass                     │
│                                                 │
│         [Step Inside →] [Take a Tour]          │
│                                                 │
│  [Subtle leaf silhouettes, amber light rays]    │
│                                                 │
├─────────────────────────────────────────────────┤
│  Features: Pricing Transparency | Community    │
├─────────────────────────────────────────────────┤
│  [Recent Harvests - Product Carousel]           │
└─────────────────────────────────────────────────┘
```

**Background:** Deep forest green with warm amber light rays
**Animation:** Condensation slowly clearing, leaves gently swaying

### Product Search Page

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Search: "What's growing today?"    [Filters ▼]│
├──────────────────────────┬──────────────────────┤
│                          │                      │
│  Filters:                │  Results (Grid)      │
│  ┌─────────────────┐    │  ┌────┐ ┌────┐       │
│  │ Garden Type     │    │  │    │ │    │       │
│  │ ○ Indica        │    │  │Card│ │Card│       │
│  │ ○ Sativa        │    │  │    │ │    │       │
│  │ ○ Hybrid        │    │  └────┘ └────┘       │
│  │                 │    │  ┌────┐ ┌────┐       │
│  │ Potency         │    │  │    │ │    │       │
│  │ ☑ 15-20%        │    │  │Card│ │Card│       │
│  │ ☑ 20-25%        │    │  │    │ │    │       │
│  │                 │    │  └────┘ └────┘       │
│  │ Price Range     │    │                      │
│  │ [Slider]        │    │                      │
│  └─────────────────┘    │                      │
└──────────────────────────┴──────────────────────┘
```

### Product Detail Page

**Structure:**
```
┌─────────────────────────────────────────────────┐
│  ← Back to Garden                              │
├──────────────────────────┬──────────────────────┤
│                          │                      │
│  [Large product image]   │  Northern Lights     │
│  (on branch, glass bg)   │  ─────────────────   │
│                          │  Indica Hybrid       │
│                          │                      │
│                          │  Potency:            │
│                          │  THC: 22% | CBD: 1%  │
│                          │                      │
│                          │  Aroma & Flavor:     │
│                          │  Earthy, Pine, Sweet │
│                          │                      │
│                          │  This cultivar...    │
│                          │  [full description]  │
│                          │                      │
│                          │  [🌿 Add to List]     │
└──────────────────────────┴──────────────────────┤
│  Available at These Gardens:                    │
│  [Dispensary cards with prices]                 │
├─────────────────────────────────────────────────┤
│  Cultivator Field Notes (Reviews)               │
│  [Review cards]                                 │
└─────────────────────────────────────────────────┘
```

---

## Interactive Elements

### Loading States

**Primary:** Condensation clearing from glass (blur to sharp)
**Secondary:** Leaves unfurling (small to full size)
**Tertiary:** Greenhouse door opening (light rays intensifying)

**Animation CSS:**
```css
@keyframes condensationClear {
  0% { backdrop-filter: blur(8px); opacity: 0.6; }
  100% { backdrop-filter: blur(0); opacity: 1; }
}

@keyframes leafUnfurl {
  0% { transform: scale(0.3) rotate(-10deg); }
  100% { transform: scale(1) rotate(0deg); }
}

@keyframes greenhouseOpen {
  0% { filter: brightness(0.7); }
  100% { filter: brightness(1); }
}
```

### Hover Effects

**Product Cards:**
- Lift: `transform: translateY(-4px);`
- Glow: `box-shadow: 0 8px 24px rgba(244, 164, 96, 0.3);`
- Sway: Subtle `rotate` animation (±1deg)

**Buttons:**
- Grow: `transform: scale(1.02);`
- Brightness: `filter: brightness(1.1);`
- Glow: `box-shadow: 0 0 16px rgba(244, 164, 96, 0.5);`

### Watchlist Interaction

**Animation:** Plant being marked/tagged for harvest
1. Small ribbon/ties appear and wrap around plant
2. Wooden tag slides in with "Added to garden" message
3. Toast notification: "🌿 Marked for harvest"

### Toast Notifications

**Style:**
- Background: Semi-transparent dark green with blur
- Border: Thin warm amber
- Icon: Leaf, sprout, or small plant
- Animation: Slide up from bottom with fade in

---

## Copywriting Guidelines

### Voice & Tone

**Primary Voice:** Warm, earthy, cultivator-to-cultivator
- Helpful and knowledgeable
- Passionate but not pushy
- Insider feel without being exclusive
- Legitimate, medical-focused

### Key Phrases

**Welcoming:**
- "Step inside"
- "Welcome to the garden"
- "Utah's best-kept secret"
- "From our garden to yours"

**Product-Focused:**
- "Fresh harvest"
- "Cultivated with care"
- "What's growing today?"
- "From the greenhouse"

**Action-Oriented:**
- "Mark for harvest" (Add to watchlist)
- "Notify when ready" (Price alerts)
- "Explore the garden" (Browse)

### Strain Description Template

```
[Strain Name]
Indica/Sativa/Hybrid • [Region]

THC: [XX]% | CBD: [X]%

Aroma & Flavor:
[Earthy, pine, sweet, citrus, etc.]

Cultivation Notes:
[Growing characteristics, appearance, density]

Ideal For:
[Medical conditions] / [Wellness goals]
```

### Review Prompts

**Encourage detailed observations:**
- "What effects did you notice?"
- "Which symptoms were helped?"
- "How was the aroma and flavor?"
- "Would you recommend this harvest?"

**Avoid:**
- Slang terms ("fire," "dank," etc.)
- Consumption references
- Illegal behavior references

---

## Responsive Design

### Breakpoints

- **Mobile:** < 640px (Single column, condensed cards)
- **Tablet:** 640px - 1024px (Two columns, medium cards)
- **Desktop:** > 1024px (Three columns, full cards)

### Mobile Considerations

- Navigation: Hamburger menu with full-screen overlay
- Product cards: Stack vertically, larger touch targets
- Search: Full-width, filters in collapsible drawer
- Typography: Scale down slightly, maintain readability

---

## Accessibility

### Color Contrast

- All text meets WCAG AA (4.5:1 minimum)
- Primary text on dark: `#f5f5f0` on `#1a3c28`
- Amber CTAs: `#1a3c28` text on `#f4a460` background

### Focus States

- Visible amber ring: `outline: 2px solid #f4a460;`
- High contrast outline on dark backgrounds
- Keyboard navigation fully supported

### Screen Readers

- ARIA labels for icon-only buttons
- Semantic HTML (headings, landmarks)
- Descriptive alt text for product images
- Skip to main content link

---

## Implementation Notes

### Tailwind CSS Configuration

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        greenhouse: {
          dark: '#1a3c28',
          medium: '#2d5a3d',
          light: '#4ade80',
        },
        wood: {
          light: '#d4a574',
          medium: '#8b6f47',
          dark: '#3d2914',
        },
        sunlight: {
          DEFAULT: '#f4a460',
          bright: '#fbbf24',
        },
      },
      fontFamily: {
        display: ['Playfair Display', 'serif'],
        body: ['Inter', 'sans-serif'],
        handwritten: ['Caveat', 'cursive'],
      },
      backgroundImage: {
        'glass-pattern': "url('/textures/glass-condensation.png')",
        'wood-grain': "url('/textures/wood-grain.png')",
        'leaf-pattern': "url('/textures/leaf-pattern.png')",
      },
      animation: {
        'sway': 'sway 3s ease-in-out infinite',
        'unfurl': 'leafUnfurl 0.6s ease-out',
        'clear': 'condensationClear 0.8s ease-out',
      },
    },
  },
}
```

### Icon Library

**Recommended:** Lucide React or Heroicons
- **Leaf/pharmacy:** Plant, sprout, leaf icons
- **Greenhouse:** Warehouse, building, home icons
- **Sunlight:** Sun, sparkles, glow effects
- **Navigation:** Arrow, menu, search icons

### Image Assets Needed

- **Backgrounds:** Glass textures, wood grain, leaf patterns
- **Illustrations:** Greenhouse scenes, plant silhouettes
- **Product placeholders:** Branch with empty tag/frame
- **Empty states:** "No plants found" illustrations

---

## Legal & Compliance

### Appropriateness

**The "Greenhouse" metaphor is ideal because:**
- Cultivation is legal and legitimate in Utah's medical market
- Focuses on **growth** and **agriculture**, not consumption
- Emphasizes **botanical properties** and **medical value**
- "Secret" = pricing transparency, not illegal access

### Required Compliance

Every page must include:
> "This website is for informational purposes only. We do not sell controlled substances. Utah Medical Cannabis Cardholders 21+ only."

### Copy Guidelines

✅ **Acceptable:**
- "Cultivated for medical use"
- "Grown by licensed Utah cultivators"
- "Strains for pain relief, anxiety, etc."
- "Harvested and tested for quality"

❌ **Avoid:**
- Consumption references ("smoke," "toke," etc.)
- Slang ("fire," "dank," "loud," etc.)
- Illegal behavior references
- Glorification of intoxication

---

## Future Enhancements

### Phase 2 Features
- **Virtual Greenhouse Tour:** Interactive 3D greenhouse experience
- **Cultivator Profiles:** Meet the growers behind each garden
- **Harvest Calendar:** Seasonal availability tracker
- **Growth Timeline:** Visual lifecycle of each strain
- **"My Garden" Dashboard:** Personalized watchlist with plant metaphors

### Gamification Elements
- **Green Thumb Badge:** For helpful reviewers
- **Harvest Streak:** For weekly price checkers
- **Cultivator Level:** Unlock features through engagement
- **Rare Specimen Finder:** Badge for discovering low-stock items

---

## References & Inspiration

**Visual Inspiration:**
- Secret garden concept art
- Botanical greenhouse photography
- Warm, amber-lit interior spaces
- Wood texture and grain patterns
- Glass condensation macro photography

**Web Design References:**
- Warm, earthy e-commerce sites
- Botanical illustration portfolios
- Nature-focused app designs
- Agricultural brand websites

**Color Palette Generators:**
- Coolors.co (search: "forest," "greenhouse," "wood")
- Adobe Color (forest green + amber themes)
- Tailwind shade generator for consistent palettes

---

## Summary

**The Secret Greenhouse** is a warm, inviting theme that frames cannabis discovery as accessing a hidden cultivation sanctuary. It uses organic metaphors (growth, harvest, gardens) to stay within legal medical boundaries while creating a memorable, exclusive experience.

**Key Strengths:**
- Unique concept not seen in cannabis websites
- Naturally organic and earthy aesthetic
- Greenhouse metaphor is legal and appropriate
- Warm, welcoming tone that builds trust
- High memorability and brand potential

**Best For:**
- Passion projects wanting to stand out
- Medical cannabis markets needing legitimacy
- Brands emphasizing cultivation and quality
- Audiences valuing authenticity and warmth
