# Spec: Site Redesign — Part 1: Foundation + Shell

> Generated from: `.vibeflow/prds/site-redesign-nextjs.md`
> Date: 2026-04-15

## Objective

Bootstrap a Next.js 15 static site in `site/` with the Obsidian Purple x Claude Orange design system, shadcn/ui, and the page shell (navbar + hero + footer) — so Parts 2 and 3 can drop in section components without touching config or layout.

## Context

The repo is a Claude Code plugin (markdown-only, no build tooling). The current landing page is a monolithic `index.html` at root. This part creates the entire Next.js project from scratch in `site/`, sets up the design system, and delivers the three most structurally important sections: navbar, hero (with graph canvas), and footer. These form the "shell" that all other sections slot into.

## Definition of Done

1. **Builds and exports**: `cd site && npm run build` succeeds and produces `site/out/index.html` with `output: 'export'` in `next.config.ts`
2. **Design tokens**: `globals.css` defines the full purple x orange palette from the PRD (all 17 tokens) as CSS custom properties, mapped to Tailwind via `@theme`
3. **Navbar renders**: Fixed navbar with blurred backdrop, Bedrock logo/wordmark, 4 anchor links (How It Works, Skills, Use Cases, Install), and a GitHub star badge linking to the repo
4. **Hero renders**: Full-viewport hero with (a) animated graph canvas (ported from current `index.html` but with fewer nodes, lower opacity, slower speed), (b) gradient headline using `--gradient-hero`, (c) one-line tagline, (d) terminal block with copy-to-clipboard, (e) two CTA buttons (Get Started gradient + View on GitHub ghost)
5. **Footer renders**: GitHub star button, license text, author credit, links to README and repo
6. **Responsive**: Navbar collapses to hamburger on mobile (<768px); hero headline scales down; footer stacks vertically. No horizontal overflow at 375px, 768px, or 1440px
7. **No stray colors**: Every color in the rendered page traces back to the design token palette — no hardcoded hex values outside `globals.css`

## Scope

- `site/` directory with Next.js 15, TypeScript, Tailwind CSS v4, shadcn/ui
- `site/package.json`, `site/next.config.ts`, `site/tsconfig.json`
- `site/app/globals.css` — design tokens, font imports (Inter + JetBrains Mono), base styles
- `site/app/layout.tsx` — root layout with metadata, font loading, navbar + footer wrapper
- `site/app/page.tsx` — renders Hero; placeholder `<section>` stubs for Parts 2-3
- `site/components/navbar.tsx` — fixed nav with backdrop blur, logo, links, GitHub badge
- `site/components/hero.tsx` — full-viewport hero with canvas, headline, terminal, CTAs
- `site/components/graph-canvas.tsx` — `<canvas>` animation extracted as its own component (client component with `useEffect`)
- `site/components/terminal-block.tsx` — reusable terminal UI with copy-to-clipboard (used in hero and later in installation section)
- `site/components/footer.tsx`
- `site/lib/utils.ts` — shadcn `cn()` utility
- shadcn/ui components: `Button`, `Badge` (installed via CLI)
- `site/public/` — empty for now (GIF placeholders come in Part 2)

## Anti-scope

- No "How It Works", "Skills Showcase", "Use Cases", "Vault Demo", or "Installation" sections — those are Parts 2 and 3
- No Framer Motion animations yet — static rendering only (animations are Part 3)
- No light theme toggle — dark only
- No mobile hamburger menu *interactivity* (the collapsed nav just hides links, no drawer) — interactivity can be refined in Part 3
- No GitHub API call for real star count — static badge linking to repo
- No CI/CD or GitHub Pages deployment config — just the build

## Technical Decisions

| Decision | Alternative | Justification |
|---|---|---|
| `site/` subdirectory, not root | Monorepo with turborepo | The plugin must stay at root (Claude Code resolves `.claude-plugin/` from cwd). A subdirectory is the simplest isolation with zero config overhead. |
| Next.js 15 with `output: 'export'` | Vite + React, Astro | User chose Next.js explicitly. Static export means no server, same as a Vite build, but with Next.js ecosystem (Image optimization, metadata API). |
| Tailwind CSS v4 (CSS-first config) | Tailwind v3 with `tailwind.config.js` | v4 uses `@theme` in CSS — design tokens live in `globals.css` alongside custom properties. One source of truth for the palette. |
| Graph canvas as separate client component | Inline in hero, or use a library (tsparticles) | Isolation keeps the hero component clean. No library — the existing vanilla canvas code from `index.html` works well and has zero dependencies. |
| `TerminalBlock` as reusable component | Inline terminal markup in each section | Used in both Hero and Installation (Part 3). Extract once, reuse. |
| Inter + JetBrains Mono via `next/font` | Google Fonts CDN, system fonts | `next/font` self-hosts with zero layout shift. Inter for body (clean, neutral), JetBrains Mono for code (developer audience). |

## Applicable Patterns

This is a greenfield web project — none of the existing `.vibeflow/patterns/` (skill-architecture, entity-definition, etc.) apply directly. However:

- **Naming**: Component files use kebab-case (`terminal-block.tsx`), matching the plugin's filename convention
- **No new patterns introduced**: This is standard Next.js + shadcn/ui project structure

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `output: 'export'` breaks with shadcn/ui components that need server features | Low | shadcn/ui is client-friendly. Avoid any server-only APIs. Test `next build` early. |
| Graph canvas performance on mobile | Medium | Reduce node count and disable animation on `prefers-reduced-motion`. Use `requestAnimationFrame` with proper cleanup. |
| Tailwind v4 breaking changes vs shadcn/ui expectations | Medium | shadcn/ui recently added v4 support. Pin versions. If issues arise, fall back to v3 config. |
