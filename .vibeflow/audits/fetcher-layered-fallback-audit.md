## Audit Report: Layered Fallback Fetcher Architecture

**Verdict: PASS**

> Audited on 2026-04-15 against `.vibeflow/specs/fetcher-layered-fallback.md`

### Tests

No test runner detected (markdown-only Claude Code plugin, no build system). Verify manually that fetchers work end-to-end by running `/bedrock:teach` with a Confluence or Google Docs URL.

### DoD Checklist

- [x] **1. Renamed** — `skills/confluence-to-markdown/` and `skills/gdoc-to-markdown/` exist with SKILL.md and scripts/extract.js. Old directories `skills/confluence/` and `skills/gdoc/` do not exist (verified via `ls -d`).

- [x] **2. 3-layer structure** — Both SKILL.md files implement the required structure in order:
  - Confluence: Step 1 (Parse URL) → Step 2 (Layer 1: MCP Atlassian) → Step 3 (Layer 2: API REST) → Step 4 (Layer 3: Browser) → Output Contract → Hard Rules → Troubleshooting
  - GDocs: Step 1 (Parse URL and Detect Type) → Step 2 (Layer 1: MCP Google Docs) → Step 3 (Layer 2: API with sub-strategies A/B) → Step 4 (Layer 3: Browser) → Output Contract → Hard Rules → Troubleshooting

- [x] **3. MCP layer behavior** — Confluence fetcher Step 2 attempts `plugin:atlassian:atlassian` MCP via ToolSearch, with 3-way branching: tools found+authed → use, tools found+unauthed → guide + ask user, tools not found → log + fall through. GDocs fetcher Step 2 checks for Google Docs/Drive MCP, notes "this is the expected case today" for not found, and falls through to Layer 2. Both ask the user before skipping on unconfigured MCP.

- [x] **4. Auth guidance standardized** — All guidance messages across both fetchers follow the format `> **{Layer} not available/failed/not authenticated:** {reason}. {instruction}. {fallback}.` Verified 7 guidance messages in Confluence fetcher and 10 in GDocs fetcher, all consistent.

- [x] **5. Teach updated** — `skills/teach/SKILL.md` references:
  - Line 56: `skills/confluence-to-markdown/SKILL.md`
  - Line 57: `skills/gdoc-to-markdown/SKILL.md`
  - Line 103: `<base_dir>/../confluence-to-markdown/SKILL.md`
  - Line 113: `<base_dir>/../gdoc-to-markdown/SKILL.md`
  - Line 305 (Critical Rules): both new paths referenced
  - Fallback descriptions updated to mention "MCP → API → browser" layers
  - Grep confirms zero references to old paths `../confluence/` or `../gdoc/` in skills/

- [x] **6. Sync updated** — `skills/sync/SKILL.md` Phase 2 sections 2.1 and 2.2 now use the internal "read SKILL.md and follow instructions" pattern:
  - Line 136: `Read the internal fetcher at <base_dir>/../confluence-to-markdown/SKILL.md`
  - Line 144: `Read the internal fetcher at <base_dir>/../gdoc-to-markdown/SKILL.md`
  - Previous external skill invocations (`Invoke skill /confluence-to-markdown`, `Invoke skill /gdoc-to-markdown`) replaced

- [x] **7. Conventions compliance** — Both fetcher SKILL.md files have:
  - YAML frontmatter with `name`, `description`, `user_invocable`, `allowed-tools` (skill-architecture pattern)
  - Stepped structure with numbered sections (skill-architecture pattern)
  - Hard Rules table (skill-architecture pattern)
  - `user_invocable: false` (skill-delegation pattern — internal modules)
  - Kebab-case directory names (vault-writing-rules naming convention)
  - Confluence `extract.js` unchanged (MD5 `1330e65baf409b8147f23d654bb046ef` matches original)
  - No violations of conventions.md Don'ts detected

### Pattern Compliance

- [x] **skill-architecture.md** — Both fetcher SKILL.md files follow the pattern: YAML frontmatter with required fields, step-by-step structure (Step 1-4 instead of Phase 1-4, appropriate for internal modules), Hard Rules table at the end, Troubleshooting table. Evidence: `confluence-to-markdown/SKILL.md:1-9` (frontmatter), `:276-287` (Hard Rules), `:291-303` (Troubleshooting). Same structure in `gdoc-to-markdown/SKILL.md`.

- [x] **skill-delegation.md** — Both fetchers are internal modules that return data to callers, never write to the vault. Output Contract sections specify return format (Markdown content + metadata). Evidence: `confluence-to-markdown/SKILL.md:265-272`, `gdoc-to-markdown/SKILL.md:367-384`. Hard Rules include "Read-only" constraint in both.

- [x] **vault-writing-rules.md** — Naming conventions followed: kebab-case directory names (`confluence-to-markdown`, `gdoc-to-markdown`), lowercase filenames. Not directly applicable beyond naming since fetchers are read-only.

### Convention Violations

None detected.

### Budget

Files changed: 4 / 4 budget (confluence-to-markdown/SKILL.md, gdoc-to-markdown/SKILL.md, teach/SKILL.md, sync/SKILL.md) + 2 supporting scripts (extract.js files, excluded per spec).

### Anti-scope Verified

- No new fetcher types added
- preserve/compress/query/setup untouched
- Confluence extract.js content unchanged (MD5 verified)
- No entity definition or template changes
- Output contract preserved (Markdown + metadata return format)
- No graphify integration changes
- No .vibeflow/index.md changes
