# Saving Optimizer — Brand Kit (site v1)

This file documents the locked brand used on the static website. Keep it next to the site so Hostinger uploads stay consistent.

## Positioning

Practical guides for Canadians who want to keep more of what they earn — without the jargon.

## Audience

Middle-aged men and women in Canada saving across everyday life: Food & Groceries, Transportation, Housing, Utilities, Kids, Clothing, Personal Care, Travel, Personal Finance, Insurance, Healthcare, Household Items and Supplies, Pets, Subscriptions, Entertainment, Students, Weddings, Events, Education, Technology, Internet, and Sports.

## Logo

- **Official logo (approved 3 Oct 2026): the Saving Optimizer moose.** A cartoon brown moose in a green toque dropping a `$` coin into a green piggy bank, with the charcoal "Saving Optimizer" wordmark.
- **Header:** `assets/logo-header.webp` with `assets/logo-header.png` fallback (493×112, shown at 56px tall on desktop, 50px on tablet, 46px on mobile). Alt text: `Saving Optimizer`.
- **Icon:** moose head in a green circle (JSON-LD logo). Favicons use the moose head on a solid white (`#FFFFFF`) background (changed 6 Oct 2026): `favicon.ico` (16/32/48, site root), `assets/favicon-32.png`, `assets/favicon-16.png`, `assets/apple-touch-icon.png` (180), `assets/android-chrome-192.png`, `assets/android-chrome-512.png`, listed in `site.webmanifest`.
- **Structured data logo:** `assets/logo-moose-512.png` (Organization and Publisher `logo` in JSON-LD).
- **Default share image:** `assets/og-default.jpg` (1200×630, stacked moose logo on white), used for `og:image`, `twitter:image` and the default Article `image`.
- Masters (transparent PNGs, including the full header, stacked logo and 800×800 icon) live outside the site in `brand/moose/final/`.
- The artwork is raster. A vector trace was tried and rejected because it lost the shading and added artefacts, so do not swap in an SVG trace.

Do not recolour, stretch or redraw the moose. The old green `$` circle (`assets/logo-primary.png`, `assets/favicon.svg`) is retired and kept only so old external links still resolve.

## Colour palette

| Role | Name | Hex | Use |
|------|------|-----|-----|
| Primary | Savings Green | `#0F7A4B` | CTAs, accents, logo circle, links |
| Background | White | `#FFFFFF` | Page backgrounds, cards |
| Soft fill | Soft Grey | `#F3F4F6` | Section bands, subtle panels |
| Secondary | Mid Grey | `#6B7280` | Secondary text, captions |
| Text | Near Black | `#1A1A1A` | Headings, body, wordmark |
| Border (supporting) | — | `#E5E7EB` | Hairline borders only |

**Rule:** white backgrounds by default. Green for emphasis and action only — buttons, links, kickers, and the mark. Do not flood sections in green.

Hover green for buttons: `#0C643D`. Soft green wash for icon pills and nav hover: `#E7F4EE`.

## Typography

- **Font:** Inter from Google Fonts, weights 400 / 500 / 600 / 700
- **Fallback:** `system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
- **Headings:** Inter semibold/bold, tight letter-spacing
- **Body:** Inter regular, ~17px, line-height 1.7

## Voice

- Clear, calm, Canadian (TFSA, RRSP, provincial energy and transit context where relevant)
- Practical over hype — real dollars, real trade-offs
- Friendly coach, not a bank ad
- Speak to busy adults optimizing household spending
- No lorem ipsum, no US-only circulars, no get-rich-quick

## Content categories (locked set)

1. Food & Groceries
2. Transportation
3. Housing
4. Utilities
5. Kids
6. Clothing
7. Personal Care
8. Travel
9. Personal Finance
10. Insurance
11. Healthcare
12. Household Items and Supplies
13. Pets
14. Subscriptions
15. Entertainment
16. Students
17. Weddings
18. Events
19. Education
20. Technology
21. Internet
22. Sports

## Website principles

- White canvas, grey structure, green accents
- Generous whitespace, clear hierarchy
- Mobile-first static HTML/CSS/JS (no build step)
- Accessible: skip link, focus states, labelled forms, semantic HTML5
- Cards lift slightly on hover; “coming soon” cards stay dashed and static
