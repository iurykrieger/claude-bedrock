# Spec: Default Obsidian Configuration for Vault Setup

> Generated via /vibeflow:gen-spec on 2026-04-13
> PRD: `.vibeflow/prds/obsidian-default-config.md`
> Budget: ≤ 4 files (project default) — this spec touches **1 file**

## Objective
After running `/bedrock:setup`, users open the vault in Obsidian and immediately see a color-coded graph view with 7 distinct colors for each entity type, wikilinks configured as the default link format, and a minimal plugin setup — with zero manual configuration.

## Context
The setup skill (`skills/setup/SKILL.md`) currently creates entity directories, templates, `.bedrock/config.json`, vault `CLAUDE.md`, and example entities — but no `.obsidian/` configuration. Users must manually configure link behavior, disable noise plugins, and set up 7 color groups in the graph view. Since every entity template includes `tags: [type/<type>]`, the graph view can query these tags to colorize nodes automatically.

Obsidian stores configuration in `.obsidian/` as JSON files. The graph view uses `graph.json` with a `colorGroups` array where each entry has a `query` (using Obsidian's search syntax `tag:#type/actor`) and a `color` object with `a` (alpha, float) and `rgb` (packed integer: `R*65536 + G*256 + B`).

## Definition of Done

- [ ] **1. Graph colors work:** `graph.json` includes 7 `colorGroups` entries with visually distinct colors, each querying `tag:#type/<entity>` (actor, person, team, topic, discussion, project, fleeting). Opening graph view shows colored nodes without manual config.
- [ ] **2. Wikilinks enforced:** `app.json` sets `useMarkdownLinks: false` and `newLinkFormat: "shortest"` — matching Bedrock's bare `[[name]]` convention.
- [ ] **3. Clean defaults:** `appearance.json` configures a sensible base theme. `core-plugins.json` enables only the `graph` plugin (minimal set required for the color groups to be usable).
- [ ] **4. Idempotent:** Each of the 4 config files is checked independently — if a file already exists in `.obsidian/`, it is skipped (never overwritten). The setup summary reports which files were created vs. skipped.
- [ ] **5. Setup integration:** New Phase 3.5 added to `skills/setup/SKILL.md` between Phase 3.4 (CLAUDE.md) and Phase 3.5 (Example Entities, renumbered to 3.6). Skipped when `RECONFIGURE_MODE = true`. Follows the skill architecture pattern.
- [ ] **6. No conventions.md violations:** No path-qualified wikilinks, no flat tags, no sensitive data. Config files use only standard Obsidian JSON schema fields.

## Scope

### File touched
- `skills/setup/SKILL.md` — add Phase 3.5 (Obsidian Configuration)

### Phase 3.5 — Create Obsidian Configuration

> **Skip if `RECONFIGURE_MODE = true`.** (Same as 3.1, 3.2, and the current 3.5)

**Step 1:** Create `.obsidian/` directory:
```bash
mkdir -p .obsidian
```

**Step 2:** For each config file below, check if it exists. If it does, skip it and log `"Skipped .obsidian/<file> — already exists"`. If it doesn't, create it with the content specified.

#### `.obsidian/app.json`
```json
{
  "useMarkdownLinks": false,
  "newLinkFormat": "shortest",
  "strictLineBreaks": false,
  "showFrontmatter": true
}
```
- `useMarkdownLinks: false` — Obsidian uses wikilinks by default (matches Bedrock's `[[name]]` convention)
- `newLinkFormat: "shortest"` — generates bare `[[name]]` links without path prefix (matches Bedrock's "bare wikilinks only" rule)
- `showFrontmatter: true` — frontmatter is central to Bedrock entities; visible by default helps users understand the schema

#### `.obsidian/appearance.json`
```json
{
  "baseFontSize": 16,
  "theme": "obsidian"
}
```
- `theme: "obsidian"` — Obsidian's built-in dark theme. Clean, high-contrast, and widely preferred for knowledge work.

#### `.obsidian/graph.json`
```json
{
  "collapse-filter": true,
  "search": "",
  "showTags": false,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": false,
  "colorGroups": [
    {
      "query": "tag:#type/actor",
      "color": { "a": 1, "rgb": 4886745 }
    },
    {
      "query": "tag:#type/person",
      "color": { "a": 1, "rgb": 5294200 }
    },
    {
      "query": "tag:#type/team",
      "color": { "a": 1, "rgb": 15241530 }
    },
    {
      "query": "tag:#type/topic",
      "color": { "a": 1, "rgb": 10181046 }
    },
    {
      "query": "tag:#type/discussion",
      "color": { "a": 1, "rgb": 15844367 }
    },
    {
      "query": "tag:#type/project",
      "color": { "a": 1, "rgb": 15158332 }
    },
    {
      "query": "tag:#type/fleeting",
      "color": { "a": 1, "rgb": 9807270 }
    }
  ],
  "collapse-display": true,
  "showArrow": false,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.5,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1,
  "close": false
}
```

**Color palette (7 entity types):**

| Entity | Tag query | Hex | RGB int | Semantic |
|---|---|---|---|---|
| actor | `tag:#type/actor` | `#4A90D9` | `4886745` | Blue — systems, technical, stable |
| person | `tag:#type/person` | `#50C878` | `5294200` | Green — people, human, organic |
| team | `tag:#type/team` | `#E8913A` | `15241530` | Orange — organizational, warm |
| topic | `tag:#type/topic` | `#9B59B6` | `10181046` | Purple — subjects, themes, abstract |
| discussion | `tag:#type/discussion` | `#F1C40F` | `15844367` | Gold — conversations, highlights |
| project | `tag:#type/project` | `#E74C3C` | `15158332` | Red — initiatives, urgency, deadlines |
| fleeting | `tag:#type/fleeting` | `#95A5A6` | `9807270` | Grey — temporary, muted, raw |

Key graph settings:
- `collapse-color-groups: false` — color groups panel starts expanded so users can see and understand the color mapping immediately
- `showTags: false` — tag nodes are hidden to keep the graph focused on entity nodes (tags would add visual noise)
- `showOrphans: true` — orphan entities are visible (important for vault health visibility)

#### `.obsidian/core-plugins.json`
```json
["graph"]
```
- Only `graph` enabled. This is the minimum required for the color groups to work. All other core plugins are disabled for a clean experience.

**Step 3:** Log results for the setup summary (Phase 4):
```
### Obsidian Configuration
| File | Status |
|---|---|
| .obsidian/app.json | Created / Skipped (already exists) |
| .obsidian/appearance.json | Created / Skipped (already exists) |
| .obsidian/graph.json | Created / Skipped (already exists) |
| .obsidian/core-plugins.json | Created / Skipped (already exists) |
```

### Setup summary update (Phase 4)

Add `.obsidian/` files to the "Files Created" table and add a note to the "What's Next?" section:

```markdown
> **Tip:** The graph view is preconfigured with 7 colors — one for each entity type.
> Open Graph View (Ctrl/Cmd+G) to see your entities color-coded by type.
> Customize colors in Graph View → Groups if you prefer different colors.
```

### Phase renumbering

Current Phase 3.5 (Create Example Entities) becomes **Phase 3.6**. The new Obsidian Configuration phase is **Phase 3.5**. Update the internal reference in Phase 3.5.7 (Verify Bidirectional Links) to 3.6.7 accordingly.

## Anti-scope
- No community plugins (Dataview, Templater) — future enhancement
- No `workspace.json` — layout is screen-size dependent
- No `hotkeys.json` — personal preference
- No knowledge-node color group — they inherit actor's blue via folder proximity
- No `status/*` or `domain/*` tag colors — only `type/*` in v0
- No Obsidian theme installation — built-in theme only
- No `.obsidian/` creation during `RECONFIGURE_MODE` — only fresh setup

## Technical Decisions

| Decision | Trade-off | Justification |
|---|---|---|
| Enable `graph` core plugin despite "no plugins" request | Slightly conflicts with PRD's "all disabled" intent | Without `graph` enabled, the color groups in `graph.json` are useless. The user's primary goal is a colored graph — enabling the one plugin needed for that is the right call. |
| Use `tag:#type/<entity>` query syntax | Alternative: `tag:type/<entity>` without `#` | Obsidian forum examples show `tag:#tagname` is the standard syntax. The `#` is Obsidian's tag prefix. Both may work, but `tag:#` is more widely documented. |
| Dark theme (`"obsidian"`) as default | Could use light theme (`"moonstone"`) | Dark theme is more commonly preferred for knowledge work, better contrast for colored graph nodes, and "obsidian" is the app's namesake theme. Users can change via Settings. |
| RGB as packed integer (not hex) | Less readable than hex strings | This is Obsidian's native format. `rgb = R*65536 + G*256 + B`. Converting to hex for human readability is done only in the spec table. |
| Per-file idempotency (not all-or-nothing) | Slightly more complex logic | If a user has customized `graph.json` but not `app.json`, we should still create `app.json`. All-or-nothing would skip everything if any file exists. |
| `showTags: false` in graph | Tags visible could help some users | Tag nodes in the graph create visual noise (7 tag nodes for `type/*` alone). Entities are the primary graph content. Users can toggle this on. |

## Applicable Patterns

| Pattern | How it applies |
|---|---|
| **Skill Architecture** (`patterns/skill-architecture.md`) | New phase follows the standard structure: numbered phase, clear objective, skip condition (`RECONFIGURE_MODE`), step-by-step instructions. |
| **Vault Writing Rules** (`patterns/vault-writing-rules.md`) | Tags are hierarchical (`type/actor`). The graph queries match this exact format. `app.json` enforces the wikilink convention. |
| **Template Structure** (`patterns/template-structure.md`) | Every template includes `tags: [type/<type>]` — this is what the graph color queries match. No template changes needed. |

No new patterns introduced.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| `tag:#type/actor` query syntax doesn't work in some Obsidian versions | Colors don't appear in graph | Spec includes alternative syntax `tag:type/actor` (without `#`). If testing shows `#` doesn't work, switch. Low risk — forum examples confirm `tag:#` syntax. |
| Obsidian changes `graph.json` schema in a future version | Config silently ignored or errors | Obsidian is backward-compatible with config — unknown fields are ignored. The JSON structure has been stable since v1.0. |
| Users expect all core plugins (file explorer, search) to be enabled | Confusion when sidebar is empty | The "What's Next?" section guides users. They can enable plugins via Settings. This is an intentional minimal-by-default choice. |
| RGB integer values are wrong (calculation error) | Wrong colors displayed | Hex-to-int conversion is verified in the spec table. Implementer should double-check one value: `#4A90D9` → `74*65536 + 144*256 + 217 = 4886745`. |
