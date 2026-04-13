# PRD: Landing Page

> Generated via /vibeflow:discover on 2026-04-13

## Problem
The Bedrock plugin has no public-facing page beyond a plain GitHub README. Potential users scrolling through GitHub or linked from social media see a wall of markdown with no visual hook — they can't quickly grasp what Bedrock does, why it matters, or how to get started. A polished landing page is the difference between "I'll check this out later" (never) and "let me install this right now."

## Target Audience
Developers and knowledge workers who already use **Obsidian** and **Claude Code** (or are curious about either). They land on the page from GitHub, Twitter/X, or a direct link. They want to understand the value proposition in under 30 seconds and install in under 60.

## Proposed Solution
A single self-contained HTML file (`index.html`) at the repo root, deployable via GitHub Pages with zero build steps. The page includes:

1. **Hero section** — animated 3D knowledge graph background (CSS/Canvas, inspired by the Obsidian graph view: colored nodes, subtle connection lines, slow drift animation on dark `#1e1e1e` background). Overlaid: headline, one-liner description, and a prominent CTA (`claude plugins add iurykrieger/claude-bedrock`).
2. **Skill workflow section** — visual step-by-step showing the recommended skill usage order (setup → teach → preserve → query → compress → sync), with brief descriptions.
3. **Use cases section** — 3-4 concrete scenarios (engineering team wiki, product management, open source project docs, personal second brain) with short descriptions.
4. **Installation section** — copy-pasteable install command with a code block, plus the `--plugin-dir` alternative for local dev.
5. **Skills grid** — cards for each of the 6 skills with name, icon/emoji, and one-line purpose.
6. **Footer** — GitHub star link/button, license, author credit.

Design language: dark theme (matching Obsidian's dark mode), clean typography, smooth scroll, mobile-responsive.

## Success Criteria
- Page loads with no external dependencies (no CDN, no npm, no build step)
- All 6 sections render correctly on desktop and mobile (responsive)
- The animated graph background runs smoothly (60fps on modern browsers)
- A user can understand what Bedrock does and how to install it within 30 seconds of landing
- GitHub Pages deployment works by simply enabling it on the repo (no config needed beyond selecting root)

## Scope v0
- Single `index.html` file with inline CSS and JS
- Animated canvas-based knowledge graph hero (nodes + edges, multi-colored, slow drift)
- 6 content sections as described above
- Dark theme, responsive layout
- Copy-to-clipboard on install command
- GitHub star link in footer

## Anti-scope
- No framework (React, Astro, Tailwind, etc.)
- No build step or package.json
- No external fonts, CDNs, or third-party scripts
- No demo GIF or video production (the animated graph IS the visual)
- No analytics or tracking
- No blog, changelog, or docs pages — this is a single page
- No dark/light theme toggle — dark only
- No i18n — English only
- No custom domain setup

## Technical Context
- The repo has zero build tooling — it's a Claude Code plugin made entirely of markdown files
- The graph animation should use `<canvas>` for performance (CSS-only would struggle with 100+ nodes)
- Color palette for nodes should match the Obsidian graph view: blues, reds, greens, yellows, cyan on `#1e1e1e` background with `rgba` connection lines
- The 6 skills and their descriptions are already documented in `README.md` and `CLAUDE.md`
- GitHub repo URL: `https://github.com/iurykrieger/claude-bedrock`
- Install command: `claude plugins add iurykrieger/claude-bedrock`

## Open Questions
None.
