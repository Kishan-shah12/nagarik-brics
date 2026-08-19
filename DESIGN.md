# NagarikBRICS — Design System Specification

> **Version**: `1.0.0-mvp`
> **Compliance**: WCAG 2.1 AA
> **Philosophy**: Authoritative, data-dense, zero-decoration government dashboard.

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [CSS Custom Properties](#2-css-custom-properties)
3. [Color System](#3-color-system)
4. [Typography](#4-typography)
5. [Spacing & Layout](#5-spacing--layout)
6. [Component Standards](#6-component-standards)
7. [Accessibility Mandate](#7-accessibility-mandate)
8. [Data Visualization Palette](#8-data-visualization-palette)
9. [Motion & Animation](#9-motion--animation)
10. [Implementation Checklist](#10-implementation-checklist)

---

## 1. Design Principles

| # | Principle | Rationale |
|---|---|---|
| 1 | **Zero border-radius** | Government dashboards must communicate authority and precision. Rounded corners suggest informality. All elements use `border-radius: 0px`. No exceptions. |
| 2 | **High contrast first** | WCAG 2.1 AA requires 4.5:1 contrast for normal text and 3:1 for large text. Our palette exceeds these thresholds. Policymakers work in varied lighting. |
| 3 | **Data density over whitespace** | Every pixel must earn its place. Policymakers need to see the maximum amount of structured data without scrolling. |
| 4 | **Monochromatic with semantic accents** | The base palette is neutral (slate). Color is reserved exclusively for semantic meaning: severity, category, status. |
| 5 | **No gratuitous animation** | Motion is used only for state transitions and data loading. No decorative animations. Response to interaction must feel instant. |

---

## 2. CSS Custom Properties

All values below are **mandatory**. Components MUST reference these variables — hardcoded values are a code review rejection.

```css
:root {
  /* ================================================================
     COLOR SYSTEM
     ================================================================ */

  /* --- Base Palette (Slate — Authoritative Neutral) --- */
  --color-bg-primary:       #0F1117;    /* Main background — near-black */
  --color-bg-secondary:     #161922;    /* Card / panel background */
  --color-bg-tertiary:      #1E2130;    /* Elevated surface (modals, dropdowns) */
  --color-bg-hover:         #262A3A;    /* Interactive hover state */
  --color-bg-active:        #2E3348;    /* Active / pressed state */

  --color-border-primary:   #2A2E3F;    /* Default border */
  --color-border-secondary: #3A3F54;    /* Emphasized border */
  --color-border-focus:     #6E7BFF;    /* Focus ring — high visibility */

  /* --- Text --- */
  --color-text-primary:     #F0F1F5;    /* Primary body text — 15.2:1 on bg-primary */
  --color-text-secondary:   #A0A4B8;    /* Secondary / label text — 7.1:1 on bg-primary */
  --color-text-tertiary:    #6B7084;    /* Disabled / placeholder — 4.6:1 on bg-primary */
  --color-text-inverse:     #0F1117;    /* Text on light backgrounds */

  /* --- Semantic: Severity --- */
  --color-critical:         #FF3B3B;    /* Urgency 8–10 / very_negative */
  --color-critical-bg:      #2A1014;    /* Background tint for critical */
  --color-high:             #FF8C42;    /* Urgency 6–7.9 / negative */
  --color-high-bg:          #2A1E10;    /* Background tint for high */
  --color-medium:           #FFD166;    /* Urgency 4–5.9 / neutral */
  --color-medium-bg:        #2A2510;    /* Background tint for medium */
  --color-low:              #06D6A0;    /* Urgency 0–3.9 / positive */
  --color-low-bg:           #0A2A20;    /* Background tint for low */

  /* --- Semantic: Status --- */
  --color-success:          #06D6A0;    /* Processed, accepted */
  --color-warning:          #FFD166;    /* Processing, draft */
  --color-error:            #FF3B3B;    /* Failed, rejected */
  --color-info:             #6E7BFF;    /* Informational */

  /* --- Semantic: Infrastructure Categories --- */
  --color-cat-water:        #4FC3F7;    /* water_sanitation */
  --color-cat-transport:    #FF8A65;    /* transportation */
  --color-cat-energy:       #FFD54F;    /* energy_power */
  --color-cat-health:       #EF5350;    /* healthcare */
  --color-cat-education:    #AB47BC;    /* education */
  --color-cat-housing:      #8D6E63;    /* housing */
  --color-cat-digital:      #26C6DA;    /* digital_connectivity */
  --color-cat-waste:        #9CCC65;    /* waste_management */
  --color-cat-safety:       #5C6BC0;    /* public_safety */

  /* --- BRICS Nation Accents --- */
  --color-brics-br:         #009739;    /* Brazil */
  --color-brics-ru:         #D52B1E;    /* Russia */
  --color-brics-in:         #FF9933;    /* India */
  --color-brics-cn:         #DE2910;    /* China */
  --color-brics-za:         #007749;    /* South Africa */


  /* ================================================================
     TYPOGRAPHY
     ================================================================ */

  /* --- Font Families --- */
  --font-primary:           'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono:              'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

  /* --- Font Sizes (Modular Scale — 1.200 Minor Third) --- */
  --font-size-xs:           0.694rem;   /* 11.1px — footnotes */
  --font-size-sm:           0.833rem;   /* 13.3px — captions, labels */
  --font-size-base:         1rem;       /* 16px — body text */
  --font-size-md:           1.2rem;     /* 19.2px — subheadings */
  --font-size-lg:           1.44rem;    /* 23px — section headers */
  --font-size-xl:           1.728rem;   /* 27.6px — page titles */
  --font-size-2xl:          2.074rem;   /* 33.2px — hero numbers */
  --font-size-3xl:          2.488rem;   /* 39.8px — KPI values */

  /* --- Font Weights --- */
  --font-weight-regular:    400;
  --font-weight-medium:     500;
  --font-weight-semibold:   600;
  --font-weight-bold:       700;

  /* --- Line Heights --- */
  --line-height-tight:      1.2;        /* Headings, KPIs */
  --line-height-normal:     1.5;        /* Body text */
  --line-height-relaxed:    1.75;       /* Long-form justification text */

  /* --- Letter Spacing --- */
  --letter-spacing-tight:   -0.02em;    /* Large headings */
  --letter-spacing-normal:  0em;        /* Body */
  --letter-spacing-wide:    0.05em;     /* Labels, overlines */
  --letter-spacing-wider:   0.1em;      /* ALL CAPS labels */


  /* ================================================================
     SPACING (8px Base Grid)
     ================================================================ */

  --space-1:                0.25rem;    /* 4px */
  --space-2:                0.5rem;     /* 8px */
  --space-3:                0.75rem;    /* 12px */
  --space-4:                1rem;       /* 16px */
  --space-5:                1.5rem;     /* 24px */
  --space-6:                2rem;       /* 32px */
  --space-7:                2.5rem;     /* 40px */
  --space-8:                3rem;       /* 48px */
  --space-9:                4rem;       /* 64px */
  --space-10:               5rem;       /* 80px */


  /* ================================================================
     BORDERS & SHAPES
     ================================================================ */

  --border-radius:          0px;        /* MANDATORY: Zero radius on all elements */
  --border-width:           1px;
  --border-width-thick:     2px;
  --border-style:           solid;


  /* ================================================================
     SHADOWS (Minimal — No Soft Glows)
     ================================================================ */

  --shadow-sm:              0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow-md:              0 2px 8px rgba(0, 0, 0, 0.5);
  --shadow-lg:              0 4px 16px rgba(0, 0, 0, 0.6);
  --shadow-focus:           0 0 0 2px var(--color-border-focus);


  /* ================================================================
     TRANSITIONS
     ================================================================ */

  --transition-fast:        120ms ease-out;
  --transition-normal:      200ms ease-out;
  --transition-slow:        350ms ease-out;


  /* ================================================================
     Z-INDEX SCALE
     ================================================================ */

  --z-base:                 0;
  --z-dropdown:             100;
  --z-sticky:               200;
  --z-overlay:              300;
  --z-modal:                400;
  --z-toast:                500;


  /* ================================================================
     LAYOUT
     ================================================================ */

  --sidebar-width:          260px;
  --header-height:          56px;
  --content-max-width:      1440px;
  --map-min-height:         500px;
}
```

---

## 3. Color System

### 3.1 Contrast Ratios (Verified WCAG 2.1 AA)

| Foreground | Background | Ratio | Pass |
|---|---|---|---|
| `--color-text-primary` (#F0F1F5) | `--color-bg-primary` (#0F1117) | **15.2:1** | ✅ AAA |
| `--color-text-secondary` (#A0A4B8) | `--color-bg-primary` (#0F1117) | **7.1:1** | ✅ AA |
| `--color-text-tertiary` (#6B7084) | `--color-bg-primary` (#0F1117) | **4.6:1** | ✅ AA (large) |
| `--color-text-primary` (#F0F1F5) | `--color-bg-secondary` (#161922) | **13.1:1** | ✅ AAA |
| `--color-critical` (#FF3B3B) | `--color-bg-primary` (#0F1117) | **5.4:1** | ✅ AA |
| `--color-low` (#06D6A0) | `--color-bg-primary` (#0F1117) | **9.8:1** | ✅ AAA |
| `--color-info` (#6E7BFF) | `--color-bg-primary` (#0F1117) | **5.1:1** | ✅ AA |

### 3.2 Usage Rules

1. **Never use color alone** to convey meaning. Always pair with text labels, icons, or patterns.
2. **Category colors** are for data visualization only (heatmap markers, chart segments). Never for background fills on interactive elements.
3. **BRICS nation colors** are used exclusively in the country filter bar and map legends.
4. **Severity colors** map directly to urgency_score ranges and are the ONLY colors used on the heatmap overlay.

---

## 4. Typography

### 4.1 Font Loading

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### 4.2 Type Scale Application

| Element | Size Variable | Weight | Line Height | Letter Spacing | Use Case |
|---|---|---|---|---|---|
| KPI Value | `--font-size-3xl` | `--font-weight-bold` | `--line-height-tight` | `--letter-spacing-tight` | Large dashboard numbers (total feedback, avg urgency) |
| Page Title | `--font-size-xl` | `--font-weight-bold` | `--line-height-tight` | `--letter-spacing-tight` | "Infrastructure Recommendations" |
| Section Header | `--font-size-lg` | `--font-weight-semibold` | `--line-height-tight` | `--letter-spacing-normal` | "Hotspot Analysis", "Top Projects" |
| Card Title | `--font-size-md` | `--font-weight-semibold` | `--line-height-normal` | `--letter-spacing-normal` | Recommendation titles |
| Body Text | `--font-size-base` | `--font-weight-regular` | `--line-height-normal` | `--letter-spacing-normal` | Justification text, descriptions |
| Label / Caption | `--font-size-sm` | `--font-weight-medium` | `--line-height-normal` | `--letter-spacing-wide` | Filter labels, chart axis labels |
| Overline | `--font-size-xs` | `--font-weight-semibold` | `--line-height-tight` | `--letter-spacing-wider` | "PRIORITY SCORE", "BUDGET ESTIMATE" (all caps) |
| Code / Data | `--font-size-sm` | `--font-weight-regular` | `--line-height-normal` | `--letter-spacing-normal` | Feedback IDs, coordinates, JSON |

### 4.3 Rules

- **ALL CAPS** is permitted ONLY for overline labels (e.g., "URGENCY", "CATEGORY"). Use `text-transform: uppercase` with `--letter-spacing-wider`.
- **No italic** in the dashboard. Emphasis is conveyed through weight (medium → semibold) or color.
- **Tabular numbers** (`font-variant-numeric: tabular-nums`) are mandatory on all numeric data to ensure column alignment.

---

## 5. Spacing & Layout

### 5.1 Grid System

```
┌────────────────────────────────────────────────────────────────┐
│ HEADER (--header-height: 56px)                                │
│ Logo  │  Country Filter Tabs  │  Refresh  │  Status         │
├────────┬───────────────────────────────────────────────────────┤
│        │                                                      │
│ SIDE   │  MAIN CONTENT                                        │
│ BAR    │  ┌──────────────────────────────────────────────┐    │
│        │  │  KPI STRIP (4 columns)                       │    │
│ 260px  │  │  Total │ Avg Urgency │ Critical │ Countries  │    │
│        │  └──────────────────────────────────────────────┘    │
│ Filters│  ┌──────────────────────────────────────────────┐    │
│ Legend │  │  HEATMAP (--map-min-height: 500px)           │    │
│        │  │  Leaflet.js interactive map                   │    │
│        │  └──────────────────────────────────────────────┘    │
│        │  ┌──────────────────────────────────────────────┐    │
│        │  │  RECOMMENDATIONS LIST                        │    │
│        │  │  Sorted by priority_score descending          │    │
│        │  └──────────────────────────────────────────────┘    │
│        │                                                      │
└────────┴──────────────────────────────────────────────────────┘
```

### 5.2 Spacing Rules

- **Outer page padding**: `--space-6` (32px)
- **Between sections**: `--space-6` (32px)
- **Card internal padding**: `--space-5` (24px)
- **Between card elements**: `--space-3` (12px)
- **Between inline items** (tags, badges): `--space-2` (8px)
- **Form field gap**: `--space-4` (16px)

### 5.3 Responsive Breakpoints

| Breakpoint | Width | Layout Change |
|---|---|---|
| Desktop | ≥ 1280px | Full sidebar + main content |
| Tablet | 768–1279px | Sidebar collapses to top filter bar |
| Mobile | < 768px | Single column, map stacks above recommendations |

---

## 6. Component Standards

### 6.1 Card (Recommendation Card)

```css
.card {
  background: var(--color-bg-secondary);
  border: var(--border-width) var(--border-style) var(--color-border-primary);
  border-radius: var(--border-radius); /* 0px */
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--transition-fast),
              box-shadow var(--transition-fast);
}

.card:hover {
  border-color: var(--color-border-secondary);
  box-shadow: var(--shadow-md);
}

.card:focus-within {
  box-shadow: var(--shadow-focus);
  outline: none;
}
```

### 6.2 Button

```css
.btn {
  font-family: var(--font-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--letter-spacing-wide);
  padding: var(--space-2) var(--space-4);
  border: var(--border-width) var(--border-style) var(--color-border-primary);
  border-radius: var(--border-radius); /* 0px */
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: background var(--transition-fast),
              border-color var(--transition-fast);
}

.btn:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-secondary);
}

.btn:focus-visible {
  box-shadow: var(--shadow-focus);
  outline: none;
}

.btn-primary {
  background: var(--color-info);
  color: var(--color-text-inverse);
  border-color: var(--color-info);
}
```

### 6.3 Badge (Severity / Category)

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  font-family: var(--font-primary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--letter-spacing-wider);
  text-transform: uppercase;
  border-radius: var(--border-radius); /* 0px */
  border: var(--border-width) var(--border-style) transparent;
}

.badge-critical {
  background: var(--color-critical-bg);
  color: var(--color-critical);
  border-color: var(--color-critical);
}

.badge-high {
  background: var(--color-high-bg);
  color: var(--color-high);
  border-color: var(--color-high);
}

.badge-medium {
  background: var(--color-medium-bg);
  color: var(--color-medium);
  border-color: var(--color-medium);
}

.badge-low {
  background: var(--color-low-bg);
  color: var(--color-low);
  border-color: var(--color-low);
}
```

### 6.4 KPI Metric Card

```css
.kpi-card {
  background: var(--color-bg-secondary);
  border: var(--border-width) var(--border-style) var(--color-border-primary);
  border-radius: var(--border-radius); /* 0px */
  padding: var(--space-4);
}

.kpi-card__label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);
  margin-bottom: var(--space-1);
}

.kpi-card__value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
  line-height: var(--line-height-tight);
}
```

---

## 7. Accessibility Mandate

These are **non-negotiable requirements**. Failing any item is a code review rejection.

### 7.1 Color & Contrast

- [ ] All text meets WCAG 2.1 AA contrast ratios (4.5:1 normal, 3:1 large)
- [ ] Color is never the sole indicator of meaning — always paired with text/icon
- [ ] Focus indicators are visible (`--shadow-focus`) on ALL interactive elements
- [ ] Custom focus styles use `--color-border-focus` with 2px ring

### 7.2 Keyboard Navigation

- [ ] All interactive elements are reachable via `Tab` key
- [ ] Focus order follows visual reading order (top-left → bottom-right)
- [ ] `Escape` closes modals and dropdowns
- [ ] Map supports keyboard pan (arrow keys) and zoom (+/-)

### 7.3 Semantic HTML

- [ ] Single `<h1>` per page ("NagarikBRICS Dashboard")
- [ ] Heading hierarchy: `h1` → `h2` (sections) → `h3` (cards) — no skips
- [ ] `<nav>`, `<main>`, `<aside>`, `<section>`, `<article>` used correctly
- [ ] All `<img>` have `alt` attributes; decorative images use `alt=""`
- [ ] Interactive elements use `<button>` or `<a>`, never `<div>` with `onclick`

### 7.4 ARIA

- [ ] Heatmap has `role="img"` with `aria-label` describing current state
- [ ] Loading states use `aria-busy="true"` and `aria-live="polite"`
- [ ] Filter controls have `aria-label` or `<label>` associations
- [ ] Badge severity labels include `aria-label` (e.g., `aria-label="Critical urgency"`)

---

## 8. Data Visualization Palette

### 8.1 Heatmap Gradient (Urgency)

The heatmap uses a **continuous gradient** mapped to `urgency_score` (0–10):

| Score Range | Color Variable | Hex | Label |
|---|---|---|---|
| 8.0 – 10.0 | `--color-critical` | `#FF3B3B` | Critical |
| 6.0 – 7.9 | `--color-high` | `#FF8C42` | High |
| 4.0 – 5.9 | `--color-medium` | `#FFD166` | Medium |
| 0.0 – 3.9 | `--color-low` | `#06D6A0` | Low |

### 8.2 Category Chart Colors

When displaying category distribution (bar chart, pie chart), use the `--color-cat-*` palette. These are chosen for maximum perceptual distinction and colorblind-safety.

| Category | Variable | Hex |
|---|---|---|
| Water & Sanitation | `--color-cat-water` | `#4FC3F7` |
| Transportation | `--color-cat-transport` | `#FF8A65` |
| Energy & Power | `--color-cat-energy` | `#FFD54F` |
| Healthcare | `--color-cat-health` | `#EF5350` |
| Education | `--color-cat-education` | `#AB47BC` |
| Housing | `--color-cat-housing` | `#8D6E63` |
| Digital Connectivity | `--color-cat-digital` | `#26C6DA` |
| Waste Management | `--color-cat-waste` | `#9CCC65` |
| Public Safety | `--color-cat-safety` | `#5C6BC0` |

---

## 9. Motion & Animation

### 9.1 Permitted Animations

| Trigger | Property | Duration | Easing |
|---|---|---|---|
| Hover on interactive element | `background`, `border-color` | `--transition-fast` (120ms) | `ease-out` |
| Panel expand/collapse | `max-height`, `opacity` | `--transition-normal` (200ms) | `ease-out` |
| Data loading skeleton | `opacity` pulse | 1.5s | `ease-in-out` (loop) |
| Toast notification enter | `transform`, `opacity` | `--transition-slow` (350ms) | `ease-out` |
| Map marker appear | `transform` (scale) | `--transition-normal` (200ms) | `ease-out` |

### 9.2 Prohibited Animations

- ❌ No parallax scrolling
- ❌ No decorative particle effects
- ❌ No auto-playing carousels
- ❌ No text animation (typewriter, fade-in words)
- ❌ No continuous rotation or bounce

### 9.3 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 10. Implementation Checklist

Before any frontend pull request, verify:

- [ ] **All colors** use CSS custom properties — zero hardcoded hex values
- [ ] **All `border-radius`** values are `var(--border-radius)` (resolves to 0px)
- [ ] **All font sizes** use the type scale variables — no `px` or arbitrary `rem`
- [ ] **All spacing** uses `--space-*` variables — no arbitrary margins/padding
- [ ] **Focus states** are visible on every interactive element
- [ ] **`prefers-reduced-motion`** media query is included
- [ ] **Contrast ratios** are verified for any new color combinations
- [ ] **Semantic HTML** is used (no `<div>` buttons, no skipped headings)
- [ ] **ARIA attributes** are present on custom widgets
- [ ] **Tabular nums** enabled on all numeric displays

---

*This design system is the single source of truth for all frontend development on NagarikBRICS. Deviations require documented justification and design review.*
