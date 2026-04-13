---
tags: [skill, plugin, claude-code, phased-execution, markdown]
modules: [skills/]
applies_to: [skills]
confidence: inferred
---
# Pattern: Skill Architecture

<!-- vibeflow:auto:start -->
## What
Each skill is a single `SKILL.md` file containing YAML frontmatter (name, description, allowed-tools) followed by a multi-phase procedural prompt that guides Claude Code through a complete workflow.

## Where
All 6 skills live in `skills/<name>/SKILL.md`: query, teach, preserve, compress, sync, setup.

## The Pattern
Every skill follows a consistent structure:

1. **YAML frontmatter** with `name`, `description`, `user_invocable: true`, and `allowed-tools` restricting which tools the skill can use.
2. **Plugin Paths section** — mandatory boilerplate explaining how to resolve entity definitions and templates relative to `<base_dir>`.
3. **Overview section** — brief description of the skill's role and a declaration of agent type ("You are a [read-only|execution|setup] agent").
4. **Numbered Phases** — each phase has a clear objective, step-by-step instructions, and expected outputs. Phases are always sequential (Phase 0, 1, 2...).
5. **Critical Rules table** — a `| Rule | Detail |` table at the end summarizing hard constraints.

Key conventions:
- Phase 0 is always `git pull --rebase origin main` (vault sync) for write skills.
- User confirmation is required before any write operation (Fase 3 → "Confirma?").
- Git commit + push happens in the final phase with retry logic (max 2 attempts).
- Best-effort for external sources — never block the workflow.

## Rules
- Skills MUST declare `allowed-tools` to restrict tool access
- Skills MUST include the "Plugin Paths" section for path resolution
- Phase numbering is sequential; sub-phases use decimal notation (1.1, 1.2, 2.1)
- Each skill declares its agent type in the overview (read-only, execution, setup)
- Write skills require explicit user confirmation before executing changes
- All skills support `source_url` and `source_type` for provenance tracking

## Examples from this codebase
File: skills/preserve/SKILL.md
```yaml
---
name: preserve
description: >
  Ponto unico de escrita no vault. Centraliza deteccao de entidades, matching textual,
  criacao/atualizacao de entidades e vinculacao bidirecional.
user_invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, mcp__plugin_github_github__*, mcp__plugin_atlassian_atlassian__*
---
```

File: skills/query/SKILL.md
```yaml
---
name: query
description: >
  Skill de leitura inteligente do vault. Recebe uma pergunta em linguagem natural...
user_invocable: true
allowed-tools: Bash, Read, Glob, Grep, Skill, Agent, mcp__plugin_github_github__get_file_contents, mcp__plugin_github_github__list_commits, mcp__plugin_github_github__list_pull_requests
---
```

File: skills/teach/SKILL.md (Phase structure example)
```markdown
## Fase 1 — Detectar e Ler Fonte
### 1.1 Classificar o input
...
## Fase 2 — Carregar Contexto do Vault
### 2.1 Ler entity definitions
...
## Fase 3 — Analisar Conteudo e Extrair Entidades
### 3.3 Apresentar ao usuario para confirmacao
...
## Fase 4 — Delegar Entidades ao /bedrock:preserve
...
## Fase 5 — Relatorio
```
<!-- vibeflow:auto:end -->

## Anti-patterns (if found)
- The sync skill at 1,056 lines is significantly longer than others, combining 3 different modes (sources, people, github) in one file. This could become harder to maintain as complexity grows.
