---
type: project
name: ""
aliases: []  # ["SIGLA", "Short Name"] — min 1 alias (ex: ["V2 Migration"])
description: ""
status: ""  # planning | active | blocked | completed
deadline: ""
progress: ""
blockers: []
action_items:
  - description: "Descricao do item de acao"
    status: "todo"  # todo | in_progress | done | blocked
    deadline: "YYYY-MM-DD"
    owner: "[[first-last]]"
focal_points: ["[[first-last]]"]
related_topics: ["[[YYYY-MM-type-slug]]"]
related_actors: ["[[repo-name]]"]
related_teams: ["[[squad-name]]"]
sources: []  # [{url: "https://...", type: "confluence|gdoc|github-repo|csv|markdown|manual", synced_at: YYYY-MM-DD}]
updated_at: YYYY-MM-DD
updated_by: ""
tags: [type/project]  # + status/{planning,active,blocked,completed} + domain/* opcional
---

<!-- Papel Zettelkasten: index note -->
<!-- Links no corpo apontam para onde o conhecimento esta: "progresso documentado em [[2026-06-deprecation-legacy-gateway]]" — curadoria, nao repeticao -->

# Project Name

> Brief description of the project's objective and scope.

## Overview

Description of the project, its motivation, and expected outcomes.

## Status

| Field | Value |
|---|---|
| Status | planning / active / blocked / completed |
| Deadline | YYYY-MM-DD |
| Progress | description of current progress |

> **Convencao:** O status do projeto reflete uma decisao de gestao. Os action items abaixo ajudam a inferir o estado real, mas nao derivam o status automaticamente. Exemplos: se todos os items estao `done`, o projeto provavelmente esta `completed`; se algum item esta `blocked`, considere atualizar o status do projeto para `blocked`.

## Action Items

| Item | Status | Prazo | Responsavel |
|---|---|---|---|
| Descricao do item | todo | YYYY-MM-DD | [[first-last]] |

> Os action items sao definidos no frontmatter (campo `action_items`) para permitir queries Dataview. A tabela acima eh uma visualizacao para legibilidade.

**Query Dataview — items pendentes deste projeto:**

```dataview
TABLE WITHOUT ID
  item.description AS "Item",
  item.status AS "Status",
  item.deadline AS "Prazo",
  item.owner AS "Responsavel"
FROM "projects"
WHERE file.name = this.file.name
FLATTEN action_items AS item
WHERE item.status != "done"
SORT item.deadline ASC
```

## Blockers

- Blocker 1 — description and impact

## Focal Points

| Person | Role |
|---|---|
| [[first-last]] | lead |
| [[first-last]] | contributor |

## Related Topics

| Topic | Relation |
|---|---|
| [[YYYY-MM-type-slug]] | related topic |

## Related Actors

| Actor | Relation |
|---|---|
| [[repo-name]] | affected system |

## Related Teams

| Team | Relation |
|---|---|
| [[squad-name]] | owning team |

---

## Expected Bidirectional Links

> This section is a reference for agents and can be removed in real pages.

| From | To | Field |
|---|---|---|
| Project → Topic | `[[YYYY-MM-type-slug]]` | `related_topics` in frontmatter |
| Project → Actor | `[[repo-name]]` | `related_actors` in frontmatter |
| Project → Person | `[[first-last]]` | `focal_points` in frontmatter |
| Project → Team | `[[squad-name]]` | `related_teams` in frontmatter |
| Actor → Project | `[[project-slug]]` | "Related Projects" section in Actor |
| Topic → Project | `[[project-slug]]` | "Related Projects" section in Topic |
| Person → Project | `[[project-slug]]` | "Projects" section in Person |
