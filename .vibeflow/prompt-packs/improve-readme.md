# Prompt Pack: Improve README as Open-Source Project

> You are only seeing this prompt; there is no context outside it.

## Objective and Definition of Done

**Objective:** Rewrite README.md as a polished open-source project README with banner image, badges, clear value proposition, feature list, contributing guide, and license.

**Definition of Done:**
1. Banner image displayed at the top of README via `docs/banner.png`
2. README includes: value proposition, features, installation, skills table, vault structure, how it works, contributing guide, license
3. Tone is welcoming to open-source contributors
4. No broken image references or links

## Anti-scope
- Do NOT modify CLAUDE.md, skills, entities, templates, or plugin.json
- Do NOT add CI/CD configuration or GitHub Actions
- Do NOT create a LICENSE file (reference only)
- Do NOT change any plugin behavior

## Budget
- 1 file modified: `README.md`
- 1 file added: `docs/banner.png` (asset copy)

## Patterns to Follow
- File naming: kebab-case, lowercase (conventions.md)
- Project is a Claude Code plugin — markdown-only, no build system
- Repository: `https://github.com/iurykrieger/claude-bedrock`

## Where to Work
- `/README.md` — full rewrite
- `/docs/banner.png` — banner asset (copy from user-provided image)

## Directional Guidance
- Center-aligned banner and heading block with badges
- Clear "what this is" in 2 sentences below the fold
- Features as bullet list, not paragraph
- Skills table preserved from original
- Vault structure code block preserved
- Add "How It Works" section showing skill delegation flow
- Add contributing section with project structure overview
- Keep tone concise, not marketing-heavy

## How to Run/Test
No test runner — this is a markdown-only plugin. Validate by:
- Previewing README.md in a markdown renderer (GitHub, VS Code preview)
- Verifying `docs/banner.png` exists and renders
- Checking all links resolve
