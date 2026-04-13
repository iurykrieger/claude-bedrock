# Spec: Landing Page

> Generated via /vibeflow:gen-spec on 2026-04-13
> Source PRD: `.vibeflow/prds/landing-page.md`
> Budget: ≤ 4 files (using 1)

## Objective

Ship a single self-contained `index.html` that lets any visitor understand, evaluate, and install the Bedrock plugin in under 60 seconds — with an animated knowledge graph hero that visually communicates the plugin's purpose.

## Context

The repo is a Claude Code plugin made entirely of markdown. The only "marketing" surface is `README.md` — functional but not compelling. There's no build tooling, no frontend stack, and no existing HTML. This page is the first and only non-markdown file in the repo, deployed via GitHub Pages from root.

## Definition of Done

1. **`index.html` exists at repo root** and renders in Chrome/Firefox/Safari with zero console errors
2. **All 6 sections present and ordered:** hero (graph + CTA) → skill workflow → use cases → installation → skills grid → footer
3. **Canvas graph animation runs:** 80+ nodes with multi-colored palette (blue, red, green, yellow, cyan), connection lines between nearby nodes, slow drift motion, on `#1e1e1e` background
4. **Responsive layout:** content is readable and properly laid out at 375px (mobile) and 1440px+ (desktop) — no horizontal scroll, no overlapping elements
5. **Copy-to-clipboard works** on the install command block (with visual feedback on click)
6. **Zero external dependencies:** no CDN links, no `fetch()` calls, no external fonts/images/scripts — everything inline. File opens correctly from `file://` protocol

## Scope

### Hero Section
- Full-viewport `<canvas>` background with animated knowledge graph
  - 80-120 nodes: varying sizes (3px–10px radius), multi-colored (blues `#4a9eff`, reds `#ff6b6b`, greens `#51cf66`, yellows `#ffd43b`, cyan `#66d9e8`) with slight glow
  - Connection lines between nodes within proximity threshold — `rgba(255,255,255,0.06)`
  - Slow organic drift: each node has independent velocity vector, wraps around edges
  - Parallax: nodes at different "depths" (size = depth) drift at different speeds
- Overlay content (centered, z-index above canvas):
  - Plugin name: "Bedrock"
  - Tagline: "Turn any Obsidian vault into a structured Second Brain"
  - Install CTA: `claude plugins add iurykrieger/claude-bedrock` in a styled code block with copy button
  - Subtle down-arrow or scroll indicator

### Skill Workflow Section
- Horizontal pipeline showing the 6 skills in recommended order:
  `setup → teach → preserve → query → compress → sync`
- Each step: icon/emoji + skill name + one-line description
- Connected by arrows or a visual flow line
- On mobile: vertical stack instead of horizontal

### Use Cases Section
- 3-4 cards:
  - Engineering Team Wiki — Track systems, APIs, team knowledge
  - Product Management — Decisions, roadmaps, cross-team context
  - Open Source Project — Contributors, architecture, discussions
  - Personal Second Brain — Ideas, reading notes, connections
- Each card: title + 2-line description

### Installation Section
- Code block with `claude plugins add iurykrieger/claude-bedrock`
- Copy button with visual feedback (checkmark or "Copied!")
- Secondary line: "Or for local development: `claude --plugin-dir ./claude-bedrock`"
- Brief "Then run `/bedrock:setup` to initialize your vault" note

### Skills Grid
- 2x3 grid (3x2 on mobile) of cards, one per skill:
  - `/bedrock:setup` — Initialize and configure a new vault
  - `/bedrock:query` — Search and cross-reference vault entities
  - `/bedrock:teach` — Ingest from Confluence, GDocs, GitHub, CSV
  - `/bedrock:preserve` — Create and update entities with bidirectional links
  - `/bedrock:compress` — Deduplicate, consolidate, and health-check
  - `/bedrock:sync` — Re-sync entities with external sources
- Each card: skill name in monospace, one-line description, subtle icon

### Footer
- GitHub star button/link → `https://github.com/iurykrieger/claude-bedrock`
- "MIT License" + "Built by Iury Krieger"
- "Powered by Claude Code" note

## Anti-scope

- No framework, build step, or package.json
- No external fonts (use system font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`)
- No analytics, cookies, or tracking
- No dark/light toggle — dark only
- No multiple pages, routing, or SPA behavior
- No interactive demos or embedded terminals
- No image assets — the canvas animation IS the visual
- No scroll-triggered animations beyond the graph (keep it performant)

## Technical Decisions

| Decision | Choice | Why |
|---|---|---|
| Animation engine | Canvas 2D API | SVG can't handle 100+ animated elements smoothly; CSS animations lack the node-connection-distance logic. Canvas gives full control at 60fps. |
| Layout system | CSS Grid + Flexbox | Native, no framework. Grid for the skills cards, Flexbox for the workflow pipeline. |
| Font stack | System fonts | Zero external requests. `-apple-system` renders beautifully on macOS, `Segoe UI` on Windows. Monospace for code: `'SF Mono', 'Fira Code', 'Cascadia Code', monospace`. |
| Copy to clipboard | `navigator.clipboard.writeText()` | Modern API, supported in all evergreen browsers. Fallback: `document.execCommand('copy')` for older browsers. |
| Animation loop | `requestAnimationFrame` | Battery-friendly, auto-pauses when tab is not visible. |
| Responsive breakpoints | Single breakpoint at 768px | Mobile (<768px) vs desktop. Keep it simple — two layouts, not five. |
| Color scheme | Obsidian graph palette on `#1e1e1e` | Matches the product's own aesthetic. Users of Obsidian will immediately recognize the vibe. |
| Scroll behavior | `scroll-behavior: smooth` in CSS | Native smooth scroll, no JS library needed. |

## Applicable Patterns

No existing `.vibeflow/patterns/` apply — they cover skill architecture, entity definitions, and vault writing rules. This is a standalone HTML file outside the plugin's behavioral domain.

This does NOT introduce a new pattern — it's a one-off marketing page, not a repeatable structure.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Canvas animation jank on low-end devices | Poor first impression | Cap node count; use `devicePixelRatio` awareness; reduce node count on mobile (40-60 instead of 80-120) |
| Page feels empty without real screenshots/GIFs | Less convincing | The animated graph + well-written copy must carry the page. Skills grid and workflow section add density. |
| Single HTML file becomes unwieldy (>1000 lines) | Hard to maintain | Logical sections via comments (`<!-- HERO -->`, `<!-- SKILLS -->`). Acceptable trade-off for zero-dependency constraint. |
| `navigator.clipboard` blocked in some contexts | Copy button fails silently | Add `execCommand` fallback + visual error state ("Click to select") |
