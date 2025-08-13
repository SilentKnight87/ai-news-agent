## Frontend Upgrade Plan

This working plan outlines simple, high-impact UI/UX improvements to make the frontend unique, beautiful, and easy to maintain. Each section is additive with minimal refactors.

### Status
- **Completed**
  - Signature visual style
    - Added `Aurora` background using brand palette from `ai_docs/color-palette.md` (`--citrine`, `--fulvous`, `--turkey-red`, `--rosewood`, `--black-bean`).
    - Introduced `--accent` CSS var and brand palette tokens in `UI/src/app/globals.css`.
    - Wired `Aurora` into `HeroSection` background stack.
  - Premium, readable cards
    - Migrated `ArticleCard` images to `next/image` with smooth hover scale.
    - Added subtle glow ring on hover and enhanced source badge with gradient border.
    - Fixed deterministic card layout via grid rows and reserved heights for title, description, and tags. Bottom row (date + relevance) now always aligns.
  - Accessible micro‑motion
    - Respect `prefers-reduced-motion` across `HeroSection`, `ContentRow`, `ArticleCard`, `AudioPlayer`, `ArticleModal` using `useReducedMotion`.
  - FilterBar spacing polish (part of step 8)
    - Prevented control overlap: larger slider lane with inline percent label, min‑widths on selects, normalized gaps.
  - Image domains
    - Configured `UI/next.config.ts` `images.remotePatterns` for common sources.

- **In Progress / Planned**
  - Sections dock (step 3): sticky pills + anchors with basic scrollspy.
  - ContentRow ergonomics (step 6): thin top progress bar and keyboard hint on focus.
  - Typography & truncation (step 7): add `@tailwindcss/typography` + `@tailwindcss/line-clamp`, use `prose prose-invert` in modal.
  - Audio mini dock (step 5): mini variant with lightweight waveform and queue affordance.

### 1) Signature visual style
- Aurora + grain background using brand palette.
- Single accent variable used across components.

Example `Aurora` (simplified):
```tsx
// UI/src/components/Aurora.tsx
export default function Aurora() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute -top-40 -left-40 h-[60vh] w-[60vw] rounded-full blur-3xl opacity-25 bg-[conic-gradient(at_top_left,_var(--citrine),_var(--fulvous),_var(--turkey-red))]" />
      <div className="absolute top-10 right-[-10%] h-[50vh] w-[40vw] rounded-full blur-3xl opacity-20 bg-[conic-gradient(at_bottom_right,_var(--rosewood),_var(--black-bean),_var(--fulvous))]" />
    </div>
  )
}
```

### 2) Premium, readable cards
- `next/image` with blur‑up behavior, hover ring.
- Source badge with 1px gradient border.
- Deterministic layout: grid rows for title, description, tags, spacer, footer.

Key changes:
```tsx
// UI/src/components/ArticleCard.tsx (high level)
<motion.article whileHover={{ scale: 1.02 }}>
  <div className="relative h-[420px] ...">
    <div className="relative h-44 ...">
      <Image src={article.thumbnail} fill className="object-cover ..." />
    </div>
    <div className="p-5 grid grid-rows-[auto_auto_auto_1fr_auto] h-[244px]">
      {/* title / description / tags / spacer / footer(date+relevance) */}
    </div>
  </div>
</motion.article>
```

### 3) Sections dock for fast navigation (planned)
- Sticky pill bar mirroring sources; anchors to `#section-{id}`.
- Simple scrollspy to highlight active section.

### 4) Accessible micro‑motion
- `useReducedMotion` gates stagger, duration, and transforms so reduced‑motion users get instant transitions.

### 5) Audio mini dock with waveform (planned)
- Mini player docked by default; expand on click.
- Lightweight animated bars to indicate playback.
- Small “+ Queue” affordance on items with audio.

### 6) ContentRow ergonomics (planned)
- Thin progress bar on top reflecting horizontal scroll.
- Subtle keyboard hint on focus (← →).

### 7) Typography and truncation (planned)
- Add `@tailwindcss/typography` and `@tailwindcss/line-clamp`.
- Use `prose prose-invert` for long content in modal.

### 8) FilterBar polish
- Chips with counts (future), plus active filter summary when non‑default.
- Spacing fixes completed to avoid overlap.

---

### Next execution order
1. Sections dock + scrollspy (step 3)
2. ContentRow progress + keyboard hint (step 6)
3. Typography + line‑clamp plugins (step 7)
4. Audio mini dock waveform (step 5)

These can be shipped independently and tested in isolation.


