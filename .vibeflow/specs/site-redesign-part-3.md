# Spec: Site Redesign — Part 3: Demo, Installation, Animation + Polish

> Generated from: `.vibeflow/prds/site-redesign-nextjs.md`
> Date: 2026-04-15

## Objective

Complete the site with the Vault Demo section, Installation section, Framer Motion scroll animations across all sections, and responsive polish — making it production-ready for GitHub Pages deployment.

## Context

Parts 1 and 2 deliver the full shell and all interactive content sections. This part adds the final two content sections (Vault Demo and Installation), layers in scroll-triggered animations that give the page its premium feel, and does the responsive/performance pass needed before shipping.

## Definition of Done

1. **Vault Demo renders**: A styled mockup showing (a) an Obsidian-like sidebar with entity folder tree (`actors/`, `people/`, `topics/`, etc.) with 2-3 sample files per folder, and (b) a content preview panel showing a sample entity file with syntax-highlighted YAML frontmatter and wikilinks rendered as purple inline links. The mockup uses the site's design tokens (not Obsidian's actual CSS).
2. **Installation renders**: Centered section with the `TerminalBlock` component (from Part 1) showing the install command. Below it: 3 prerequisite badges (Claude Code, Obsidian, Git) as inline pill elements. A "Read the docs" link to the GitHub README.
3. **Scroll animations**: Every section (Hero, How It Works, Skills, Use Cases, Vault Demo, Installation) fades in + slides up on scroll entry using Framer Motion `whileInView`. Stagger delay on card grids and stepper items. Animations respect `prefers-reduced-motion` (disabled when set).
4. **Responsive polish**: No horizontal overflow at any breakpoint (375px, 768px, 1024px, 1440px). Touch targets ≥ 44px on mobile. Font sizes scale appropriately. The Vault Demo mockup stacks sidebar above preview on mobile.
5. **Performance**: `next build` output is <500KB total JS (excluding images). No layout shift on load (CLS < 0.1). Graph canvas pauses when not in viewport (IntersectionObserver).
6. **Craftsmanship**: No inline styles. No stray colors outside the design token palette. No `any` types in TypeScript. All interactive elements have visible focus states.

## Scope

- `site/components/vault-demo.tsx` — Obsidian-like mockup with sidebar + entity preview
- `site/components/vault-sidebar.tsx` — File tree component with folder icons and entity names
- `site/components/vault-preview.tsx` — Entity file preview with frontmatter highlighting
- `site/components/installation.tsx` — Install command + prerequisite badges
- `site/components/animate-in.tsx` — Reusable Framer Motion wrapper (`whileInView` fade+slide, with `prefers-reduced-motion` check)
- `site/data/vault-demo.ts` — Sample entity data for the mockup (folder structure + sample file content)
- Update `site/app/page.tsx` to add Vault Demo and Installation sections, wrap all sections in `AnimateIn`
- Update `site/components/graph-canvas.tsx` to pause when off-viewport (IntersectionObserver)
- Responsive adjustments across all existing components from Parts 1-2
- `site/next.config.ts` — add `basePath` if needed for GitHub Pages deployment

## Anti-scope

- No real Obsidian integration or live vault rendering — it's a static mockup
- No syntax highlighting library (Shiki, Prism) — use Tailwind classes for faux-highlighting of YAML keys and wikilinks
- No light theme
- No GitHub Actions workflow for deployment (user can set this up separately)
- No Lighthouse CI automation — manual check is sufficient for v0
- No page transitions or route animations (single page)

## Technical Decisions

| Decision | Alternative | Justification |
|---|---|---|
| Framer Motion `whileInView` | CSS `@scroll-timeline`, Intersection Observer + CSS classes | Framer Motion is already in the dependency list (from PRD). `whileInView` with `once: true` is the simplest API for scroll-triggered animations. It handles `prefers-reduced-motion` with a single prop. |
| Faux syntax highlighting with Tailwind | Shiki / Prism.js | The vault preview shows ~15 lines of YAML. A full highlighting library adds 50-100KB for 15 lines. Tailwind color classes on `<span>` elements are sufficient and zero-cost. |
| `AnimateIn` wrapper component | Inline `motion.div` on every section | A wrapper standardizes the animation (fade + 20px slide-up, 0.5s duration, `once: true`). Consistency without repetition. Accepts optional `delay` for stagger. |
| IntersectionObserver on canvas | Always-running animation | The graph canvas is GPU-intensive. Pausing it when scrolled past the hero saves battery and CPU. The observer callback toggles a `running` ref that gates `requestAnimationFrame`. |

## Applicable Patterns

- **Naming**: Consistent kebab-case components. Data files in `site/data/`.
- **Reuse**: `TerminalBlock` from Part 1 is reused in Installation. `SectionHeader` from Part 2 is reused in Vault Demo and Installation.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Vault Demo mockup looks fake/unconvincing | Medium | Use real entity data from the plugin's own `templates/` (actual frontmatter schemas). Match Obsidian's dark theme colors closely (not exactly — adapted to the site palette). |
| Framer Motion adds too much JS weight | Low | Framer Motion tree-shakes well. Only importing `motion` and `useInView`. Should add <20KB gzipped. Check bundle size in build output. |
| `basePath` for GitHub Pages breaks asset paths | Medium | Test with `basePath: '/claude-bedrock'` locally using `next start`. Ensure all internal links and image paths use `next/link` and `next/image` which respect basePath automatically. |

## Dependencies

- `.vibeflow/specs/site-redesign-part-1.md` — project scaffold, design tokens, shell, TerminalBlock
- `.vibeflow/specs/site-redesign-part-2.md` — SectionHeader component, page.tsx structure with section slots
