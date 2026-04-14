# Decision Log
> Newest first. Updated automatically by the architect agent.

## 2026-04-14 — Concept entity: permanent note, no status, flat `related_to`
- **Zettelkasten role:** permanent (not bridge). Concepts define what something IS — stable, timeless. Topics track what is HAPPENING — temporal, lifecycle-driven.
- **No `status` field:** Concepts don't have lifecycles. Temporal evolution is tracked by topics that reference concepts.
- **`related_to` array:** Single flat array instead of typed relation arrays (`actors`, `people`, etc.). Concepts relate to any entity type equally; body wikilinks provide semantic context.
- **Classification ordering:** In preserve section 1.3, concept is checked BEFORE topic fallthrough for `file_type: document/paper` nodes. This prevents concept nodes from being misclassified as topics.
