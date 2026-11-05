# UX/UI Audit Report — Addendum: Landing Page Senior Design Review

> Addendum to `Sikāi Sathi — UX UI Audit Report.pdf` (Nov 2, 2026).
> The PDF is a frozen binary, so this review is recorded here in Markdown and actioned in `frontend/index.html`.
> Date of review: Nov 2026. Scope: welcome/landing page only, judged from a desktop screenshot before a hackathon demo / production release.

## Verdict

Strong product concept, needs visual refinement. The page is functional and understandable but reads like a school assignment / instructional document rather than a polished EdTech product. It explains *how the product works* before making the user interested in using it.

## Scores (subjective design-review scores, not usability-test results)

| Dimension | Score |
|---|---|
| Visual hierarchy | 5/10 |
| Typography | 6/10 |
| Color system | 6/10 |
| Layout & spacing | 6/10 |
| Brand identity | 4/10 |
| Product communication | 5/10 |
| Visual polish | 5/10 |
| Accessibility | 6/10 |

## Findings

### 1. No coherent design system (high priority)

Maroon header, grey background, white card, blue button, green text, red numbered circles — these don't feel like one system. The maroon header and blue buttons compete.

**Recommended palette** (applied to landing page AND application):

| Token | Hex |
|---|---|
| Deep navy (brand) | `#173B67` |
| Learning blue (primary CTA) | `#2878C8` |
| Background | `#F4F7FB` |
| Surface | `#FFFFFF` |
| Success | `#22A06B` |

### 2. Documentation-style card instead of a hero (high priority)

The old page stacked 8 reading blocks (illustration → heading → paragraph → example → 4 steps → green statement → language → button) before the user could act. A landing page must answer immediately: *What is this? Why should I care? What next?*

**Recommendation:** proper hero section, CTA reachable without reading a manual.

### 3. Placeholder-feeling illustration (medium-high priority)

The balance scale is math-relevant but doesn't communicate the differentiator: *student makes a mistake → AI understands it → AI explains the misconception → student learns to solve it.*

**Recommendation:** replace with a visual of the actual product experience — an equation, an incorrect step highlighted, and a helpful correction.

### 4. Four instructional steps read like documentation (high priority)

A student shouldn't read a manual before starting. Three steps are enough:

1. **Upload your work** — Take a picture of your handwritten solution.
2. **Understand your mistake** — AI identifies where your reasoning went wrong.
3. **Learn and improve** — Get an explanation and practice similar problems.

### 5. Headline introduces instead of selling (high priority)

"सिकाइ साथीलाई चिनौँ" is not benefit-driven. Recommended copy:

- NE headline: "गल्तीबाटै सिकौँ, गणितमा अगाडि बढौँ।"
- NE sub: "तपाईंको गणितीय समाधानको फोटो खिच्नुहोस्। सिकाइ साथीले तपाईंको गल्ती पहिचान गरी, किन गल्ती भयो भनेर सरल भाषामा बुझाउँछ।"
- EN headline: "Don't just find the answer. Understand your mistakes."
- EN sub: "Upload your handwritten math solution. Sikāi Sāthī identifies your mistakes, explains why they happened, and helps you learn from them."

### 6. Language selector buried (high priority)

Language is a fundamental onboarding decision for a bilingual product. Move it to the top-right of the hero card as a compact toggle (नेपाली | English) that updates ALL interface content.

### 7. Weak CTA (high priority)

"सिक्न सुरु गर →" is acceptable but small. Recommended: "आफ्नो समाधान जाँच्नुहोस् →" / "Check My Solution →" — wider, brand-colored, 48–52px tall, the most visually important element.

## Recommended structure

1. Strong brand identity
2. Benefit-driven headline
3. Product-focused visual demonstration
4. One dominant CTA
5. Simple three-step explanation
6. Clear Nepali/English language switching

## Priority table

| Priority | Improvement | Impact |
|---|---|---|
| P0 | Redesign hero section | Very high |
| P0 | Replace illustration | Very high |
| P0 | Improve headline and CTA | Very high |
| P1 | Establish consistent colors | High |
| P1 | Simplify instructional content | High |
| P1 | Improve spacing and typography | Medium |
| P2 | Add subtle animations | Medium |
| P2 | Add testimonials or trust indicators | Medium |

## Strategic note (beyond aesthetics)

The competitive advantage is NOT solving math with AI — it is helping students understand *why they got something wrong*. Most AI math tools focus on the right answer; Sikāi Sathi focuses on the student's thinking. That distinction must be visible in the landing page, illustrations, headline, and demo within the first five seconds.

## Action taken (implementation log)

| # | Review item | Status | Implementation |
|---|---|---|---|
| 1 | Consistent palette | Done | `:root` tokens in `frontend/index.html` → navy `#173B67`, learning blue `#2878C8` (white text ≈ 4.6:1, passes AA), bg `#F4F7FB`, success `#22A06B`; `theme-color`, manifest, and `icon.svg` updated. Added `--good-ink #177245` for green *text* (pure `#22A06B` text fails 4.5:1) on trust line, success banners, done chips. Error banners now use `--err` instead of brand. |
| 2 | Hero, not docs | Done | Welcome restructured: language toggle → headline → subheading → product visual → dominant CTA → 3 steps → trust/scope. CTA sits above the fold without reading the steps. |
| 3 | Product visual | Done | Balance SVG removed; new `.w-demo` panel reuses the app's real diagnosis styling (`.badstep` + `.badflag`): `x = 15` flagged, correction strip "→ x = 5". Flag/note fully localised via `renderWelcome()`. |
| 4 | Three steps | Done | `wHow` is now 3 title+description pairs (EN/NE), rendered as `strong` + muted description on the existing timeline. |
| 5 | Headline copy | Done | Review copy applied verbatim to `wTitle`/`wLede` (EN/NE). |
| 6 | Language top-right | Done | Segmented toggle moved to `.w-top` (top-right of hero); still drives `applyI18n()` for the whole page. Visible heading replaced by `aria-label`. |
| 7 | Dominant CTA | Done, copy revised | `#wStart` → full-width, 52px, bold, brand blue + arrow. Sizing/placement per review; label later changed to "Start Your Journey" / "आफ्नो यात्रा सुरु गर्नुहोस्" (journey framing instead of "Check My Solution"). |
| P2 | Animations, testimonials | Deferred | Out of scope for this pass; sway animation removed with the old hero. |

## Open follow-ups

- **Register mix:** the review's Nepali hero copy uses formal तपाईं while the app body uses तिमी (per the earlier audit's companion tone). Validate with 5–6 students + a teacher which register the landing page should use, then unify.
- **Numeral toggle:** the static demo visual uses Latin digits regardless of the 123/१२३ toggle. Localise at render time if the toggle is kept.
- **Re-score:** re-run the 8-dimension review from a fresh screenshot after this change.
