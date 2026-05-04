---
type: code
name: ""
aliases: []  # ["Display Name", "camelCaseName"] — min 1 alias
actor: "[[actor-name]]"  # parent actor (wikilink to existing actor)
node_type: ""  # function | class | module | concept | decision | interface | endpoint
source_file: ""  # relative path inside the actor's repo (e.g. "src/Controllers/PaymentController.cs")
source_location: ""  # optional — line range like "L42-L85"
description: ""
graphify_node_ids: []  # ["billing_api_processTransaction", "billing_api_processTransactionV2"] — one or more graphify node ids grouped by semantic similarity
confidence: ""  # EXTRACTED | INFERRED | AMBIGUOUS — strongest edge confidence
relations: []  # ["[[other-code-slug]]", "[[other-actor-code-slug]]"] — optional wikilinks to related code entities
sources: []  # [{url: "https://...", type: "github-repo|graphify|manual", synced_at: YYYY-MM-DD}]
updated_at: YYYY-MM-DD
updated_by: ""
tags: [type/code]  # + domain/{...} inherited from the parent actor
---

<!-- Zettelkasten role: permanent note extension (sub-entity of actor) -->
<!-- Links in the body should have textual context when possible: "calls [[ProcessPayment]] to execute the transaction". For nodes with many relations, frontmatter `relations` is acceptable without textual context. -->

# Code Node Name

> Brief description of this node's function or role within the parent actor.

## Details

| Field | Value |
|---|---|
| Actor | [[actor-name]] |
| Node type | function / class / module / concept / decision / interface / endpoint |
| Source file | `relative/path/in/repo` |
| Source location | `L42-L85` (optional) |
| Confidence | EXTRACTED / INFERRED / AMBIGUOUS |
| Graphify node ids | `node_id_1`, `node_id_2` |

## What it does

<!-- One paragraph describing the node's responsibility. Use plain language. -->

## Relations

<!-- Wikilinks to related code entities, with textual context. Example: -->
<!-- - calls [[process-payment]] to delegate the actual charge -->
<!-- - implements the [[event-publisher-pattern]] decision documented in the parent actor -->

---

## Expected Bidirectional Links

> This section is a reference for agents and can be removed in real pages.

| From | To | Field |
|---|---|---|
| Code → Actor | `[[actor-name]]` | `actor` in frontmatter |
| Actor → Code | `[[code-slug]]` | "Knowledge Nodes" section in the parent actor |
| Code → Code | `[[other-code-slug]]` | `relations` in frontmatter or wikilink in body |
| Topic → Code | `[[code-slug]]` | "Related Code" section in topic (when applicable) |

## Graph Bridge

> The graphify nodes referenced by `graphify_node_ids` carry an optional reverse pointer
> `vault_entity_path` written by `/bedrock:preserve` Phase 6.5 (TODO — Part 3 of the
> code-graphify-bridge spec). When present, the path is relative to the vault root
> (e.g. `actors/billing-api/nodes/process-transaction.md`).
