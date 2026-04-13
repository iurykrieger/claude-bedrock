---
type: topic
title: ""
aliases: []  # ["Short Title"] — min 1 alias (ex: ["Deprecacao Probe"])
category: ""  # bugfix | troubleshooting | rfc | incident | feature | deprecation | compliance
status: ""  # open | in-progress | completed | cancelled
people: ["[[first-last]]"]
actors: ["[[repo-name]]"]
objective: ""
created_at: YYYY-MM-DD
sources: []  # [{url: "https://...", type: "confluence|gdoc|github-repo|csv|markdown|manual", synced_at: YYYY-MM-DD}]
updated_at: YYYY-MM-DD
updated_by: ""
tags: [type/topic]  # + status/{open,in-progress,completed,cancelled} + category/{deprecation,bugfix,...} + domain/* opcional
---

<!-- Papel Zettelkasten: bridge note -->
<!-- Links no corpo explicam PORQUE permanentes se relacionam: "a deprecacao do [[legacy-gateway]] esta bloqueada porque clientes do sistema legado dependem da tokenizacao do [[billing-api]]" -->

# Topic Title

> Brief description of the topic's objective.

<!-- Callout obrigatorio para topics de deprecacao: -->
<!-- > [!warning] Deprecated -->
<!-- > Descricao do plano de descontinuacao e sistemas afetados. -->

## Context

Description of context and motivation.

## People Involved

| Person | Role |
|---|---|
| [[first-last]] | focal point |
| [[first-last]] | contributor |

## Actors Involved

| Actor | Relation |
|---|---|
| [[repo-name]] | affected system |
| [[repo-name]] | replacement system |

## History

| Date | Event |
|---|---|
| YYYY-MM-DD | Event description |

## Decisions

- Decision 1 — justification

## Next Steps

- [ ] Action 1
- [ ] Action 2

---

## Expected Bidirectional Links

> This section is a reference for agents and can be removed in real pages.

| From | To | Field |
|---|---|---|
| Topic → Person | `[[first-last]]` | `people` in frontmatter |
| Topic → Actor | `[[repo-name]]` | `actors` in frontmatter |
| Person → Topic | `[[YYYY-MM-type-slug]]` | "Active Topics" in Person |
| Actor → Topic | `[[YYYY-MM-type-slug]]` | "Related Topics" in Actor |
