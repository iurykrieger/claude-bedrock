# Spec: Site Redesign — Part 2: Interactive Sections

> Generated from: `.vibeflow/prds/site-redesign-nextjs.md`
> Date: 2026-04-15

## Objective

Build the three core content sections — How It Works, Skills Showcase, and Use Cases — with interactive tab/panel patterns that break from the passive-scroll landing page convention.

## Context

Part 1 delivers the shell (navbar, hero, footer) and design system. This part fills the page body with the sections that explain *what Bedrock does* and *why you'd use it*. The Skills Showcase is the most important section — it's where GIFs of the product in action will live, and it uses a sidebar+panel layout (Resend-inspired) instead of a flat grid.

## Definition of Done

1. **How It Works renders**: A horizontal stepper showing 6 steps (`setup → teach → preserve → ask → compress → sync`). Clicking a step highlights it and reveals a panel below with (a) skill description, (b) a styled terminal snippet showing the command. Active step is visually distinct (purple accent border/background).
2. **Skills Showcase renders**: Left sidebar listing 6 skill names as clickable tabs. Right panel shows: skill name as monospace heading, 2-3 line description, a GIF placeholder (16:10 aspect ratio, dark background with "GIF coming soon" text), and the invoke command in a code block. Selecting a different tab swaps the panel content.
3. **Use Cases renders**: 4 cards in a 2x2 grid (desktop) / single column (mobile). Each card has: an icon (emoji or SVG), a title, and a 2-line description. Cards have subtle hover effect (border color shift + slight translate-Y).
4. **Content is accurate**: All skill names, descriptions, and commands match the current `README.md` and `CLAUDE.md` documentation. No invented features.
5. **Responsive**: How It Works stepper scrolls horizontally or stacks on mobile. Skills sidebar collapses to a horizontal tab bar on mobile. Use Cases stacks to 1 column. No overflow at 375px.
6. **Keyboard accessible**: Tab/Enter navigates the How It Works stepper and Skills Showcase tabs. Focus states are visible (purple ring).

## Scope

- `site/components/how-it-works.tsx` — Interactive stepper with step panels
- `site/components/skills-showcase.tsx` — Sidebar + panel layout with tab state
- `site/components/use-cases.tsx` — Card grid with hover effects
- `site/components/skill-panel.tsx` — Individual skill content panel (extracted for clarity)
- `site/components/section-header.tsx` — Reusable section label + title + subtitle (used across all three sections and reused in Part 3)
- `site/data/skills.ts` — Skill data (name, description, command, GIF path) as a typed array. Single source of truth for both How It Works and Skills Showcase.
- `site/data/use-cases.ts` — Use case data (icon, title, description) as a typed array
- `site/public/gifs/` — Directory with 6 placeholder images (one per skill)
- Update `site/app/page.tsx` to render the three new sections between Hero and Footer
- shadcn/ui components: `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`, `Card` (install via CLI if not already present)

## Anti-scope

- No Framer Motion animations on section entry — that's Part 3
- No real GIFs — placeholder images only (dark rectangles with skill name text)
- No Vault Demo or Installation sections — that's Part 3
- No horizontal scroll snap on the stepper — simple overflow-x-auto is fine
- No search or filtering on skills

## Technical Decisions

| Decision | Alternative | Justification |
|---|---|---|
| shadcn/ui `Tabs` for Skills Showcase | Custom state + divs | Tabs component handles keyboard navigation, ARIA roles, and focus management out of the box. Accessibility for free. |
| Separate `data/skills.ts` file | Inline content in components | Skills data is used in both How It Works (step names + descriptions) and Skills Showcase (full details). Single source of truth avoids drift. |
| GIF placeholders as static divs, not `<Image>` | next/image with placeholder blur | GIFs don't exist yet. Using `<Image>` with missing `src` would error. A styled `<div>` with text is simpler and makes it obvious what's missing. When GIFs arrive, swap to `<Image>` or `<video>`. |
| Skill panel as extracted component | Inline in skills-showcase.tsx | Each panel has enough content (description + GIF + command) that extracting it keeps the parent readable. |

## Applicable Patterns

- **Naming**: Data files use kebab-case in `site/data/`. Components use kebab-case in `site/components/`.
- **No new patterns introduced**.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| How It Works + Skills Showcase feel redundant (both show skills) | Medium | They serve different purposes: How It Works shows the *workflow order* (linear), Skills Showcase shows *individual skill depth* (random access). Make the visual treatment clearly distinct — stepper vs sidebar. |
| Tab state on mobile feels cramped with 6 skills | Medium | On mobile, use a horizontal scrollable tab bar (like iOS segment control). Each tab shows only the skill name abbreviation. |

## Dependencies

- `.vibeflow/specs/site-redesign-part-1.md` — requires the project scaffold, design tokens, and shell layout
