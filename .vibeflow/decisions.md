# Decision Log
> Newest first. Updated automatically by the architect agent.

## 2026-05-05 — `graph.json` promoted to primary index in `/bedrock:ask` Phase 2
- **Context:** `ask-graph-index` feature. `/bedrock:ask` used glob/grep as the primary Phase 2 search strategy, ignoring `graph.json` until Phase 3-G escalation.
- **Decision:** Phase 2.0 now reads `graph.json` nodes array first and scores by label match > community resonance > god-node boost (LLM-evaluated). Glob/grep becomes a per-term fallback for search terms with zero graph representation.
- **Scoring model:** LLM instruction, not deterministic algorithm. Rationale: SKILL.md executes as a prompt; algorithmic scoring in natural-language instructions is brittle. Semantic instructions leverage the LLM's strength.
- **Node cap:** 500 nodes from `graph.json` if array is large. Graphify orders by centrality — high-value nodes come first.
- **Phase 3-G escalation:** changed from "graph.json exists?" to "graph.json covers the specific gap?". Live `/graphify` is now a last resort. Soft gate: when in doubt, escalate.
- **Pitfall discovered:** The entity budget (15 total) is stated in two places (Phase 2.0 and Phase 2.5) without a unified accounting statement. Future spec should clarify: "15 entities total across 2.0 + 2.4 + 2.5 combined."
- **Scope clarification:** PRD initially identified "teach doesn't update graph.json" as a gap. Investigation found `/bedrock:preserve` Phase 0.2 already implements the atomic merge on every `/teach` run. No changes needed to `/teach` or `/preserve`.

## 2026-04-18 — docling promoted to core `/bedrock:teach` dependency (alongside graphify)
- **Context:** `teach-docling-integration-part-2` added docling (https://github.com/docling-project/docling) as the universal file → markdown converter inside `/teach`'s new Phase 1.5. Without docling, `/teach` is limited to markdown / text-native / CSV inputs; with it, `/teach` accepts DOCX, PPTX, XLSX, PDF, HTML, EPUB, and images.
- **Install model:** silent auto-install via `pipx` (preferred) → `pip --user` (fallback) → abort. No user confirmation prompt, matching the graphify autoinstall precedent from §1.2.1. `/bedrock:setup` installs docling at vault-init time (new §1.2.1.1); `/teach`'s Phase 0 lazily re-installs for vaults that predate this change.
- **Routing:** docling runs on every file whose extension is in docling's supported list, EXCEPT GitHub repos (which flow through clone → graphify directly). Text-native types (`.md`/`.txt`/`.csv`) and docling-unsupported types fall through as raw passthrough.
- **Failure policy:** on docling non-zero exit, raw passthrough for text-native types; abort + cleanup `$TEACH_TMP` for binary types. This deliberately breaks the "best-effort for external sources" convention because docling is a *local* dependency, not an external source.
- **Pitfall recorded:** `skills/setup/SKILL.md` Critical Rule #3 ("NEVER auto-install dependencies") is now stale — contradicted by both the graphify and docling auto-install sections. Flag for a follow-up cleanup.

## 2026-04-18 — `graphify-out/` writes route through `/bedrock:preserve` (single-write-point strengthened)
- **Context:** `teach-docling-integration-part-1` added a Phase 0.2 merge inside `/preserve` that appends incoming graphify output into the vault's cumulative `graphify-out/`. Previously `/graphify` wrote to the vault directory directly, bypassing the single-write-point pattern.
- **Decision:** all writes to `<VAULT_PATH>/graphify-out/` flow through `/bedrock:preserve`. Callers (currently `/teach`, later `/sync` if it needs append semantics) pass a `graphify_output_path` pointing at a temp directory; `/preserve` merges it into the vault.
- **Backward compat:** if `graphify_output_path` resolves to `<VAULT_PATH>/graphify-out/` itself, Phase 0.2 is a no-op. Lets legacy `/sync` callers keep working without modification.
- **Append semantics:** node-id collision unions `sources` (dedup by URL), takes most-recent `updated_at`, unions labels/tags. Edge collision keyed by `(source, target, type)` drops the duplicate. `obsidian/*.md` and `GRAPH_REPORT.md` are appended, never overwritten.
- **Stale-flag pattern:** `.graphify_analysis.json` receives a top-level `stale: true` after merge. `/preserve` never recomputes analysis inline; recomputation is delegated to `/bedrock:compress` on its next run. Keeps `/preserve` fast; accepts transient staleness in community assignments.

## 2026-04-18 — Pitfall: "zero literal matches" DoDs conflict with self-referential PRD/spec files
- **Context:** audit of `graphify-setup-autoinstall` returned PARTIAL because DoD #1 ("zero matches of `iurykrieger/graphify`") fails literally — the spec and PRD files for this feature name the bad URL to describe the bug.
- **Pitfall:** when a bug is about a literal string (bad URL, misspelled identifier, wrong constant), a DoD that demands "zero matches of `<literal>`" is structurally unsatisfiable if the spec/PRD uses that literal in its Problem/Context sections and the anti-scope forbids editing those files.
- **Guidance for future specs:** either (a) scope the "zero matches" requirement to live surfaces — e.g., "zero matches outside `.vibeflow/prds/` and `.vibeflow/specs/<this-feature>.md`" — or (b) write the spec using a placeholder (e.g., `<broken-org>/graphify`) so the literal never appears in documentation.
- **Preferred:** option (a) — keeps the spec readable and the DoD verifiable.

## 2026-04-14 — Concept entity: permanent note, no status, flat `related_to`
- **Zettelkasten role:** permanent (not bridge). Concepts define what something IS — stable, timeless. Topics track what is HAPPENING — temporal, lifecycle-driven.
- **No `status` field:** Concepts don't have lifecycles. Temporal evolution is tracked by topics that reference concepts.
- **`related_to` array:** Single flat array instead of typed relation arrays (`actors`, `people`, etc.). Concepts relate to any entity type equally; body wikilinks provide semantic context.
- **Classification ordering:** In preserve section 1.3, concept is checked BEFORE topic fallthrough for `file_type: document/paper` nodes. This prevents concept nodes from being misclassified as topics.
