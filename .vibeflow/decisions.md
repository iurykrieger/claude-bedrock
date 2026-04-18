# Decision Log
> Newest first. Updated automatically by the architect agent.

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
