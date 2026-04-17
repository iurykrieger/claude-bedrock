# PRD: Site Redesign — Next.js + shadcn/ui

> Generated via /vibeflow:discover on 2026-04-15

## Problem

The current Bedrock landing page is a monolithic 908-line `index.html` with inline CSS/JS. While functional, it follows the classic "scroll-down SaaS template" pattern — hero, features grid, CTA, footer — that immediately reads as AI-generated or template-based. It's hard to maintain, impossible to extend with new sections or pages, and doesn't showcase the product's sophistication. Bedrock is a knowledge-graph automation tool; its site should feel as intentional and crafted as the tool itself.

## Target Audience

Developers and power users who already use **Obsidian** and **Claude Code** (or are evaluating one/both). They arrive from GitHub, Twitter/X, Hacker News, or direct links. They expect a developer-tool site that respects their intelligence — not marketing fluff but clear, interactive demonstrations of what the tool does.

## Proposed Solution

A **Next.js** application using **shadcn/ui** and **Tailwind CSS v4**, deployed as a static export (`output: 'export'`) to GitHub Pages. The site replaces the single-file `index.html` with a component-based architecture.

### Design Philosophy (Resend-inspired)

The design breaks from the classic vertical-scroll landing page:

- **Dark-first** with a near-black base (`#09090b` range), not Obsidian's `#1e1e1e` — darker, more cinematic
- **Interactive panels over passive scrolling** — tabbed code examples, hover-reveal content, click-to-explore skill cards rather than a flat grid
- **Editorial typography** — large, confident headings with generous letter-spacing; body text with comfortable line-height; monospace for commands
- **Density with breathing room** — information-rich sections separated by ample whitespace, not cramped feature grids
- **Subtle motion** — Framer Motion for scroll-triggered reveals, hover micro-interactions, and tab transitions. No flashy hero animations — the graph canvas stays but becomes more restrained
- **Code as content** — real terminal sessions and vault snippets shown in styled code blocks, not abstract icons or illustrations

### Color Palette: Obsidian Purple × Claude Orange

Two signature colors blended into a cohesive palette:

| Token | Hex | Usage |
|---|---|---|
| `--purple-500` | `#a882ff` | Primary accent (links, active states, badges) — Obsidian's graph purple |
| `--purple-400` | `#c4a8ff` | Hover states, lighter text accents |
| `--purple-600` | `#7c3aed` | Darker purple for contrast elements |
| `--orange-500` | `#e8754a` | Secondary accent (CTAs, highlights, warmth) — Claude's orange |
| `--orange-400` | `#f09070` | Hover/lighter secondary |
| `--orange-600` | `#cc5a30` | Darker orange for pressed states |
| `--gradient-hero` | `#a882ff → #e8754a` | Hero gradient (purple to orange, 135deg) |
| `--gradient-subtle` | `#a882ff → #c4a8ff` | Subtle monochrome gradient for cards |
| `--bg-base` | `#09090b` | Page background |
| `--bg-card` | `#111113` | Card/panel surfaces |
| `--bg-elevated` | `#18181b` | Navbar, modals, elevated surfaces |
| `--border` | `#27272a` | Default borders (zinc-800) |
| `--text-primary` | `#fafafa` | Headings |
| `--text-secondary` | `#a1a1aa` | Body text (zinc-400) |
| `--text-muted` | `#71717a` | Captions, metadata (zinc-500) |
| `--success` | `#34d399` | Positive signals (emerald-400) |

The purple-to-orange gradient is the signature motif — used sparingly on the hero headline, CTA buttons, and accent borders. Not on every element.

### Site Sections

**1. Navbar** — Fixed, blurred backdrop. Logo (Bedrock icon + wordmark), 3-4 anchor links, GitHub star count badge, theme toggle (dark/light). Minimal — like Resend's.

**2. Hero** — Full-viewport. The animated graph canvas stays but is more subtle (fewer nodes, slower, lower opacity — atmospheric, not distracting). Over it:
- A bold headline with the purple→orange gradient on the key phrase
- One-line description
- Terminal block with install command (copy-to-clipboard)
- Two CTA buttons: "Get Started" (primary, gradient) and "View on GitHub" (ghost)

**3. How It Works** — Interactive workflow visualization (not a flat pipeline). A horizontal stepper or animated flow showing: `setup → teach → preserve → ask → compress → sync`. Clicking each step reveals a panel with a description + a real terminal/vault snippet showing the command in action. Think Resend's tabbed SDK examples.

**4. Skills Showcase** — The core section. NOT a flat 3×2 grid. Instead: a left sidebar with skill names (`/bedrock:ask`, `/bedrock:teach`, etc.) and a right panel that shows, for each selected skill:
- What it does (2-3 lines)
- A real terminal GIF or animated screenshot showing the skill in action
- The key command to invoke it

This is where the GIFs live. Interactive tab selection, not scroll.

**5. Use Cases** — 3-4 cards with real scenarios. Each card has an icon, title, 2-line description, and a subtle hover animation. Layout: 2×2 grid on desktop, stacked on mobile. Scenarios:
- Engineering team wiki (ingest Confluence → structured vault)
- Open source project knowledge base (ingest GitHub repos → entity graph)
- Personal second brain (daily notes → compressed knowledge)
- Product management (meeting notes → action items → tracked projects)

**6. Vault Demo** — A section showing the Obsidian vault output. A styled mockup of the Obsidian sidebar with entity folders, and a preview of an entity file with frontmatter + wikilinks highlighted. This could be a static screenshot or a GIF of navigating the vault. The goal: show the *output*, not just the commands.

**7. Installation** — Clean, centered section. Terminal block with the install command. Below it: 2-3 prerequisite badges (Claude Code, Obsidian, Git). A "Get Started" link to the README.

**8. Footer** — GitHub star button, license, author, links to README and CLAUDE.md.

### GIF Script (content the user needs to record)

The following GIFs should be recorded in a real Obsidian vault with Bedrock entities. Each should be 8-15 seconds, 800×500px or similar, dark Obsidian theme, smooth and deliberate mouse movements.

| # | GIF Name | What to record | Section |
|---|---|---|---|
| 1 | `setup.gif` | Run `/bedrock:setup` in Claude Code terminal → show the interactive setup wizard asking questions → vault directories being created | Skills Showcase |
| 2 | `teach.gif` | Run `/bedrock:teach <confluence-url>` → show entities being detected → files appearing in Obsidian sidebar in real-time | Skills Showcase |
| 3 | `preserve.gif` | Run `/bedrock:preserve` with a batch of entities → show files being created/updated → git commit appearing | Skills Showcase |
| 4 | `ask.gif` | Run `/bedrock:ask "what does the billing API connect to?"` → show the agent reasoning, searching the vault, returning a structured answer with wikilinks | Skills Showcase |
| 5 | `compress.gif` | Run `/bedrock:compress` → show duplicate detection → entities being merged → health report | Skills Showcase |
| 6 | `sync.gif` | Run `/bedrock:sync --github` → show repos being scanned → PRs correlated with topics → new entities created | Skills Showcase |
| 7 | `vault-navigation.gif` | Open Obsidian → navigate the vault graph view → click on an actor node → show it opening with rich frontmatter and wikilinks → click a wikilink to navigate to a connected entity | Vault Demo |
| 8 | `graph-view.gif` | Obsidian graph view fully zoomed out → slowly zoom into a cluster → show the colored nodes and connections → hover over nodes to see labels | Hero background or Vault Demo |

**Recording tips:**
- Use Obsidian's dark theme (default)
- Hide Obsidian's status bar and minimize chrome for cleaner frames
- Use a screen recording tool that outputs optimized GIFs (e.g., Kap on macOS, or record as MP4 and convert with ffmpeg)
- Keep terminal font size at 14-16px for readability
- If using Claude Code terminal, ensure the output is visible and not truncated

## Success Criteria

- Site builds and exports as static HTML via `next build` + `output: 'export'`
- Deployable to GitHub Pages via the existing release workflow (or a new `gh-pages` branch)
- Lighthouse score ≥ 90 on Performance, Accessibility, and Best Practices
- All sections render correctly on desktop (1440px), tablet (768px), and mobile (375px)
- The skills showcase section is interactive (tab/click-based), not a passive scroll grid
- Color palette consistently uses the purple×orange system — no stray colors
- Page feels premium and intentional — not template-generated
- A developer can understand what Bedrock does and how to install it within 30 seconds

## Scope v0

- Next.js 15 app with `output: 'export'` (static site)
- shadcn/ui components + Tailwind CSS v4
- Framer Motion for scroll animations and tab transitions
- 8 sections as described above
- Dark theme as default (light theme optional but not required for v0)
- Responsive layout (mobile-first)
- The 8 GIF slots with placeholder images until real GIFs are recorded
- Copy-to-clipboard on install commands
- GitHub star badge in navbar
- `site/` directory in the repo root (keeps the plugin files separate)

## Anti-scope

- No blog, changelog, or docs pages — single landing page only
- No CMS or dynamic content — all content is hardcoded in components
- No analytics, tracking, or cookies
- No i18n — English only
- No authentication or user accounts
- No API routes or server-side features (pure static export)
- No custom domain setup (GitHub Pages default)
- No light theme in v0 (can be added later — the design is dark-first)
- No video production — GIFs only, recorded by the user

## Technical Context

- The current `index.html` will be **replaced** by the Next.js site in `site/`
- The repo is a Claude Code plugin — all plugin files live at root (`skills/`, `entities/`, `templates/`, `.claude-plugin/`)
- The site lives in `site/` to avoid polluting the plugin structure
- GitHub Pages should serve from `site/out/` (the Next.js static export output)
- GitHub repo: `https://github.com/iurykrieger/claude-bedrock`
- Install command: `claude plugins add iurykrieger/claude-bedrock`
- The existing design system (CSS variables, color tokens) in the current `index.html` provides a starting reference but the palette is being overhauled
- shadcn/ui provides accessible, composable primitives (Tabs, Card, Badge, Button) that align with the interactive panel approach

## Open Questions

None.
