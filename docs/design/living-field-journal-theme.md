# The Living Field Journal - Design System Documentation

## Concept Overview

**Theme Name:** The Living Field Journal
**Core Concept:** A passionate botanist's field journal come to life - hand-drawn sketches, pressed leaves, mud on the boots, sun-drenched meadows. A researcher out in the field studying Utah's cannabis plants where they grow.

**Primary Emotion:** Curiosity, exploration, documentation, discovery
**Tone:** Naturalist, scholarly but warm, passionate observer, citizen science

---

## Visual Language

### Color Palette

#### Primary Colors
- **Sage Green** `#6b7b5c` - Primary backgrounds, headings
- **Moss Green** `#4a5d3e` - Secondary backgrounds, navigation
- **Warm Parchment** `#f4f1ea` - Main content background, paper feel
- **Terracotta** `#c17f59` - Accents, highlights, CTAs

#### Secondary Colors
- **Deep Earth Brown** `#3d2914` - Text, borders, contrast
- **Soft Beige** `#ebe7dd` - Secondary paper tones
- **Botanical Green** `#5a6f52` - Leaf illustrations, plant elements
- **Pressed Leaf Brown** `#8b7355` - Dried plant elements

#### Accent Colors
- **Field Observation Red** `#c94c4c` - Important notes, alerts
- **Watercolor Blue** `#7ab8d4` - Subtle washes, cool accents
- **Pencil Grey** `#6b7280` - Sketch lines, subtle details

### Typography

#### Headlines
- **Primary:** `Crimson Pro` or `Libre Baskerville` (elegant, scholarly serif)
- **Secondary:** `EB Garamond` (classic botanical illustration feel)
- **Usage:** Page titles, section headers, journal headers

#### Body Text
- **Primary:** `Source Serif Pro` or `Merriweather` (warm, readable serif)
- **Secondary:** `Lora` (elegant, book-like)
- **Usage:** Product descriptions, reviews, general content

#### Handwritten/Sketch
- **Primary:** `Architects Daughter` or `Kalam` (field notes feel)
- **Secondary:** `Give You Glory` (more elegant handwritten)
- **Usage:** Margin notes, specimen labels, observations

#### Monospace (Data)
- **Primary:** `Space Mono` or `Courier Prime`
- **Usage:** Specimen numbers, measurements, data points

#### Type Scale
```
H1: 2.75rem / 44px (Journal title, main header)
H2: 2rem / 32px (Page sections)
H3: 1.5rem / 24px (Card titles, specimen names)
H4: 1.125rem / 18px (Labels, field notes)
Body: 1rem / 16px (Standard text)
Small: 0.875rem / 14px (Captions, measurements)
Code: 0.875rem / 14px (Specimen numbers, data)
```

### Textures & Effects

#### Primary Textures
- **Handmade paper:** Subtle fiber texture with slight variation
- **Watercolor washes:** Soft, transparent color layers
- **Pencil strokes:** Sketch lines, graphite texture
- **Pressed leaves:** Flattened plant silhouettes with slight transparency
- **Ink bleed:** Slight spread on text, vintage document feel
- **Fabric texture:** Linen or burlap backgrounds for sections

#### Illustration Style
- **Loose botanical sketches:** Hand-drawn leaves, plants, mountains
- **Watercolor accents:** Soft color washes behind elements
- **Ink outlines:** Thin, slightly irregular pen strokes
- **Pressed leaf details:** Realistic plant pressings
- **Field map graphics:** Topographic lines, hand-drawn cartography

#### Edge Treatments
- **Torn paper edges:** Irregular, organic borders
- **Deckle edges:** Rough, handmade paper feel
- **Photo corners:** Small triangular holders (like old albums)
- **Tape/paper clips:** Holding elements to "pages"
- **Staple/pin marks:** Physical attachment simulation

---

## UI Components

### Navigation

**Design:**
- Background: Moss green (`#4a5d3e`) with subtle paper texture
- Menu items: Handwritten tab style (like bookmarked journal sections)
- Active state: Pencil underline with handwritten accent
- Hover: Small leaf doodle animates next to item, slight warmth increase
- Mobile: Slide-out with "turning page" animation

**Elements:**
```
[📖 Field Notes] [🌿 Specimens] [📍 Sites] [📋 Observations]
```

### Buttons & CTAs

**Primary Button (Field Tag):**
- Background: Terracotta (`#c17f59`) with subtle paper texture
- Border: Thin handwritten-style stroke
- Text: Warm parchment white
- Shadow: Soft drop shadow like a physical tag
- Hover: Slight lift, shadow deepens, small pencil sketch appears
- Shape: Slightly irregular (hand-cut feel)

**Secondary Button (Pencil Note):**
- Background: Transparent with pencil border
- Border: Hand-drawn sketched rectangle
- Text: Deep earth brown
- Hover: Fill with light wash (watercolor effect)

### Product Cards

**Layout:**
```
┌─────────────────────────────────────┐
│  [Paper texture with subtle grid]   │
│                                     │
│     ┌─────────────────┐             │
│     │  [Botanical    │   🏷️  #047  │
│     │   illustration] │   $45.00    │
│     │                 │   ✓ Documented│
│     │   Pressed leaf  │             │
│     │   detail        │   📊 THC 22%│
│     └─────────────────┘             │
│                                     │
│  Northern Lights                    │
│  ───────────────────                │
│  Specimen #047 • Salt Lake Region   │
│  Indica • Earthy • Pine             │
│                                     │
│  Field Notes:                       │
│  "Earthy profile with pine..."      │
│                                     │
│  [📌 Press Specimen]                │
└─────────────────────────────────────┘
```

**Animations:**
- **Idle:** Subtle page "breathing" (micro movement)
- **Hover:** Page turns slightly, lifts, reveals margin notes
- **Add to watchlist:** Pushpin appears, specimen "pressed" animation

### Search & Filters

**Search Bar:**
- Placeholder: "Search field notes..."
- Style: Pencil-outlined rectangle with paper texture
- Focus: Handwritten border darkens, small leaf doodle appears
- Icon: Magnifying glass with sketch style

**Filters:**
- Displayed as "field observation categories"
- Style: Checkbox-style with handwritten labels
- Active: Pencil checkmark, light watercolor wash
- Categories: Region, Chemotype, Potency, Harvest Season

### Dispensary Cards

**Layout:**
```
┌─────────────────────────────────────┐
│  📍 Observation Site:               │
│  Wholesome Co.                      │
│  ──────────────────────             │
│                                     │
│  [Hand-drawn field map]             │
│  with topography lines              │
│                                     │
│  Salt Lake City, UT                 │
│  Established: 2019                  │
│                                     │
│  Specimens documented: 24           │
│  Primary focus: Hybrid cultivars    │
│                                     │
│  [View Field Site →]               │
└─────────────────────────────────────┘
```

### Review Cards

**Layout:**
```
┌─────────────────────────────────────┐
│  👤 FieldObserver_3   ✓ Verified    │
│  Contributing Naturalist            │
│  ──────────────────────             │
│                                     │
│  "Documented significant pain       │
│   relief with this specimen..."     │
│                                     │
│  ⭐⭐⭐⭐⭐  (5.0)                   │
│                                     │
│  Medical: Pain relief, Sleep aid    │
│  Wellness: Relaxation, Stress reduc │
│                                     │
│  🕐 Observation logged 3 days ago    │
└─────────────────────────────────────┘
```

---

## Page Layouts

### Landing Page (Hero)

**Structure:**
```
┌─────────────────────────────────────────────────┐
│  [Navigation: Moss green, bookmarked tabs]     │
├─────────────────────────────────────────────────┤
│                                                 │
│    [Open journal spread on grass]               │
│                                                 │
│    Documenting Utah's Botanical Landscape       │
│                                                 │
│    A field study of cannabis cultivars         │
│    across Utah's medical market                │
│                                                 │
│    [Begin Field Study →] [View Specimens]      │
│                                                 │
│  [Watercolor mountains, pressed leaves]         │
│  [Distant Utah mountains sketch]                │
│                                                 │
├─────────────────────────────────────────────────┤
│  Project Goals: Documentation | Community       │
├─────────────────────────────────────────────────┤
│  [Recent Specimens - Page spread carousel]      │
└─────────────────────────────────────────────────┘
```

**Background:** Warm parchment with subtle fiber texture
**Animation:** Pages gently turning, leaves floating down, pencil sketching

### Product Search Page

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Search: "Search field notes..."    [Filters ▼]│
├──────────────────────────┬──────────────────────┤
│                          │                      │
│  Observation Parameters: │  Specimen Catalog    │
│  ┌─────────────────┐    │  ┌────┐ ┌────┐       │
│  │ Region          │    │  │    │ │    │       │
│  │ ○ Salt Lake     │    │  │Page│ │Page│       │
│  │ ○ Ogden         │    │  │    │ │    │       │
│  │ ○ Provo         │    │  │spread│spread     │
│  │                 │    │  └────┘ └────┘       │
│  │ Chemotype       │    │  ┌────┐ ┌────┐       │
│  │ ☑ Indica        │    │  │    │ │    │       │
│  │ ☑ Hybrid        │    │  │Page│ │Page│       │
│  │                 │    │  │    │ │    │       │
│  │ Potency         │    │  └────┘ └────┘       │
│  │ ☑ 15-20%        │    │                      │
│  │ ☑ 20-25%        │    │                      │
│  └─────────────────┘    │                      │
└──────────────────────────┴──────────────────────┘
```

### Product Detail Page

**Structure:**
```
┌─────────────────────────────────────────────────┐
│  ← Return to Field Notes                       │
├──────────────────────────┬──────────────────────┤
│                          │                      │
│  [Botanical illustration] │  Northern Lights     │
│  (watercolor + ink)       │  ───────────────     │
│                          │  Specimen #047       │
│  [Pressed leaf detail]    │                      │
│                          │  Taxonomy:           │
│                          │  Indica Hybrid       │
│                          │  Family: Cannabaceae │
│                          │                      │
│                          │  Field Measurements:  │
│                          │  THC: 22% | CBD: 1%  │
│                          │                      │
│                          │  Regional Profile:    │
│                          │  Earthy, Pine, Sweet │
│                          │                      │
│                          │  Field Observations:  │
│                          │  [Full description -  │
│                          │   botanical notes]    │
│                          │                      │
│                          │  [📌 Press Specimen]  │
└──────────────────────────┴──────────────────────┤
│  Documented at These Field Sites:               │
│  [Observation site cards with data]             │
├─────────────────────────────────────────────────┤
│  Contributed Field Observations (Reviews)       │
│  [Review cards as margin notes]                 │
└─────────────────────────────────────────────────┘
```

---

## Interactive Elements

### Loading States

**Primary:** Pencil sketching animation (lines drawing themselves)
**Secondary:** Page turning (flip animation with paper texture)
**Tertiary:** Leaf pressing (leaf floats down, flattens, becomes pressed)

**Animation CSS:**
```css
@keyframes pencilSketch {
  0% { stroke-dashoffset: 1000; opacity: 0; }
  100% { stroke-dashoffset: 0; opacity: 1; }
}

@keyframes pageTurn {
  0% { transform: rotateY(0deg); }
  50% { transform: rotateY(-90deg); }
  100% { transform: rotateY(0deg); }
}

@keyframes leafPress {
  0% { transform: scale(1) rotateZ(15deg); opacity: 1; }
  100% { transform: scale(0.95) rotateZ(0deg); opacity: 0.8; }
}
```

### Hover Effects

**Product Cards (Page Spreads):**
- Lift: `transform: translateY(-2px) rotateX(2deg);`
- Shadow: Soft, paper-like `box-shadow: 0 4px 12px rgba(61, 41, 20, 0.15);`
- Page reveal: Subtle 3D rotation showing margin notes

**Buttons:**
- Sketch border darkens: `border-color: #3d2914;`
- Watercolor wash fills: `background: rgba(193, 127, 89, 0.1);`
- Slight irregular movement: `transform: scale(1.02) rotate(0.5deg);`

### Watchlist Interaction

**Animation:** Pressing a specimen for the collection
1. Leaf floats down onto page
2. Flattens and becomes "pressed" (slight transparency, 2D)
3. Pushpin appears in corner
4. Toast: "📌 Specimen pressed to collection"

### Toast Notifications

**Style:**
- Background: Semi-transparent parchment with paper texture
- Border: Hand-drawn pencil stroke
- Icon: Small pencil, leaf, or clipboard
- Animation: Slide up with page flip effect

---

## Copywriting Guidelines

### Voice & Tone

**Primary Voice:** Passionate naturalist meets helpful guide
- Scholarly but approachable
- Scientific curiosity
- Warm, observational
- Community-focused (citizen science)

### Key Phrases

**Welcoming:**
- "Begin your field study"
- "Welcome to the project"
- "Documenting Utah's botanical landscape"
- "Join our community of observers"

**Product-Focused:**
- "Documented specimen"
- "Field observations"
- "Regional profile"
- "Botanical characteristics"
- "Cultivar notes"

**Action-Oriented:**
- "Press specimen" (Add to watchlist)
- "Log observation" (Write review)
- "Document when available" (Price alerts)
- "Explore field sites" (Browse dispensaries)

### Strain Description Template

```
[Strain Name]
Specimen #[ID] • [Collection Region]

Taxonomy:
Indica/Sativa/Hybrid • [Genetic lineage if known]

Field Measurements:
THC: [XX]% | CBD: [X]% | [Other cannabinoids]

Regional Profile:
[Aroma, flavor, terpene notes]

Botanical Notes:
[Growth characteristics, morphology, density]

Documented Benefits:
[Medical applications] / [Wellness effects]

Collection History:
[When/where first documented, cultivator notes]
```

### Review Prompts

**Encourage detailed observations:**
- "What effects did you document?"
- "Which symptoms were alleviated?"
- "Describe the aroma and flavor profile"
- "How did this specimen affect your condition?"

**Frame as citizen science:**
- "Add your field observations"
- "Contribute to the study"
- "Help document this cultivar"
- "Share your botanical notes"

### Avoid

❌ Slang or casual drug references
❌ Glorification of intoxication
❌ Non-scientific terminology
❌ Illegal behavior suggestions

---

## Responsive Design

### Breakpoints

- **Mobile:** < 640px (Single column, stacked pages)
- **Tablet:** 640px - 1024px (Two-column spreads)
- **Desktop:** > 1024px (Full journal layout)

### Mobile Considerations

- Navigation: Hamburger with page-flip animation
- Product cards: Single page spread, full width
- Filters: Collapsible drawer with paper texture
- Typography: Slightly smaller, maintain serif feel

---

## Accessibility

### Color Contrast

- All text meets WCAG AA (4.5:1 minimum)
- Primary text: `#3d2914` on `#f4f1ea` (high contrast)
- Terracotta CTAs: White text on `#c17f59` (verified contrast)

### Focus States

- Visible pencil outline: `outline: 2px solid #c17f59;`
- Hand-drawn style focus rings
- Keyboard navigation with visual feedback

### Screen Readers

- ARIA labels for sketch/icon buttons
- Semantic HTML (article, section, heading hierarchy)
- Descriptive alt text: "Botanical illustration of [strain]"
- Skip to content link

---

## Implementation Notes

### Tailwind CSS Configuration

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        field: {
          sage: '#6b7b5c',
          moss: '#4a5d3e',
          botanical: '#5a6f52',
        },
        paper: {
          DEFAULT: '#f4f1ea',
          light: '#ebe7dd',
          dark: '#d4cbb8',
        },
        earth: {
          brown: '#3d2914',
          terracotta: '#c17f59',
          leaf: '#8b7355',
        },
      },
      fontFamily: {
        serif: ['Crimson Pro', 'serif'],
        body: ['Source Serif Pro', 'serif'],
        handwritten: ['Architects Daughter', 'cursive'],
        mono: ['Space Mono', 'monospace'],
      },
      backgroundImage: {
        'paper-texture': "url('/textures/handmade-paper.png')",
        'watercolor-wash': "url('/textures/watercolor-wash.png')",
        'pencil-grid': "url('/textures/pencil-grid.png')",
      },
      animation: {
        'sketch': 'pencilSketch 1s ease-out',
        'page-turn': 'pageTurn 0.6s ease-in-out',
        'press': 'leafPress 0.8s ease-out',
      },
    },
  },
}
```

### Icon Library

**Recommended:** Custom SVG illustrations (hand-drawn style)
- Supplement with: Lucide React (outline style)
- **Field tools:** Clipboard, pencil, magnifying glass, map
- **Botanical:** Leaf, sprout, plant, tree
- **Documentation:** Bookmark, notebook, journal

### Image Assets Needed

- **Backgrounds:** Handmade paper, watercolor washes, pencil grids
- **Illustrations:** Botanical sketches (leaves, plants), field maps
- **Product placeholders:** Blank specimen card with illustration frame
- **Empty states:** "No specimens documented" sketches
- **UI elements:** Paper clips, tape, photo corners, pins

---

## Legal & Compliance

### Appropriateness

**The "Field Journal" metaphor works because:**
- Scientific framing is inherently legitimate
- Botanical research is appropriate for medical cannabis
- Citizen science angle makes reviews purposeful
- Focuses on **documentation** and **observation**, not consumption

### Required Compliance

Every page must include:
> "This project documents publicly available information about Utah medical cannabis. We do not sell controlled substances. For Utah Medical Cannabis Cardholders 21+."

### Copy Guidelines

✅ **Acceptable:**
- "Documented for medical research"
- "Field observations from patients"
- "Botanical study of cannabis cultivars"
- "Citizen science project documenting strains"
- "Specimen analysis and patient reports"

❌ **Avoid:**
- Consumption references
- Slang or casual terminology
- Glorification of effects
- Illegal behavior suggestions
- Non-medical framing

---

## Future Enhancements

### Phase 2 Features
- **Virtual Field Notebook:** Personal observation journal for each user
- **Botanical Illustration Gallery:** High-quality artwork downloads
- **Regional Field Maps:** Interactive maps showing strain distributions
- **Collaborative Research:** Users can contribute detailed observations
- **"Press Book":** Digital specimen collection with download/print option

### Gamification Elements
- **Field Researcher Badge:** Level up through documentation
- **Specimen Collector:** Unlock badges for documenting diverse strains
- **Citizen Scientist:** Recognition for detailed observations
- **Regional Expert:** Badges for expertise in specific areas

---

## References & Inspiration

**Visual Inspiration:**
- Vintage botanical illustration books
- Field journals from naturalists (Darwin, Audubon)
- Handmade paper and bookbinding
- Watercolor nature journals
- Scientific field notebooks

**Web Design References:**
- Notion (document-style layouts)
- Are.na (collections and research)
- Obsidian (knowledge base aesthetics)
- Digital journal apps

**Typography Resources:**
- Google Fonts (serif and handwriting categories)
- Adobe Fonts (botanical illustration styles)
- FontPair (serif + handwriting combinations)

**Illustration Style:**
- Ernst Haeckel's Art Forms in Nature
- Maria Sibylla Merian's botanical illustrations
- Modern field guide illustrations
- Scientific journal botanical plates

---

## Summary

**The Living Field Journal** is a scholarly, warm theme that frames cannabis discovery as a botanical research project. It uses scientific observation, citizen science, and vintage field journal aesthetics to create legitimacy while maintaining a personal, passionate feel.

**Key Strengths:**
- Highly unique and memorable
- Scientific framing provides legal legitimacy
- Citizen science angle makes engagement meaningful
- Warm, textured, human feel
- Educational and informative

**Best For:**
- Projects emphasizing education and research
- Medical cannabis markets requiring legitimacy
- Audiences valuing science and documentation
- Brands wanting to stand out with intellectual appeal
- Communities focused on knowledge-sharing

---

## Comparison: Secret Greenhouse vs. Living Field Journal

| Aspect | Secret Greenhouse | Living Field Journal |
|--------|------------------|---------------------|
| **Emotional tone** | Warm, exclusive, sanctuary | Curious, scholarly, exploratory |
| **Visual warmth** | Very high (amber light) | Medium-high (parchment, earth) |
| **Organic feel** | High (live plants, glass) | Very high (paper, sketches) |
| **Legal comfort** | High | Very high (scientific) |
| **Uniqueness** | High | Very high |
| **Implementation** | Medium complexity | Medium-high (illustrations) |
| **Audience appeal** | Broad (warmth is universal) | Niche (science/curiosity) |
| **Memorability** | High | High |
| **Brand potential** | High | Very high (distinctive) |
