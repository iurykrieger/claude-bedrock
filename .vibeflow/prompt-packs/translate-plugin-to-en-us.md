# Prompt Pack: Translate Plugin to en-US

> You are only seeing this prompt; there is no context outside it.

## Objective

Translate ALL content of the Bedrock Claude Code plugin from Portuguese (pt-BR) to English (en-US). This covers skills, templates, entity definitions, and documentation. The plugin turns Obsidian vaults into structured Second Brains.

## Definition of Done

- [ ] All 6 skill files (`skills/*/SKILL.md`) have frontmatter descriptions, section headers, instructions, error messages, report templates, and critical rules in English
- [ ] All 7 template files (`templates/*/_template.md`) have comments, section headers, placeholder text, and the "Expected Bidirectional Links" reference in English
- [ ] All 9 entity definition files (`entities/*.md`) are fully in English — descriptions, criteria, examples, field tables, Zettelkasten roles
- [ ] `CLAUDE.md` git convention types/verbs translated to English equivalents, all remaining pt-BR content in English
- [ ] `README.md` language rule updated (default language: English, not Portuguese)

## Anti-scope

- Do NOT touch `.vibeflow/` directory (PRDs, specs, audits — development artifacts)
- Do NOT touch `plugin.json` (already in English)
- Do NOT touch `.claude/` directory (settings)
- Do NOT change the structure or logic of any skill — only translate the natural language
- Do NOT rename files or directories
- Do NOT translate YAML frontmatter keys (they're already in English by convention)
- Do NOT translate technical terms (PCI, API, Kafka, Obsidian, Zettelkasten, graphify, etc.)
- Do NOT translate skill names or wikilink syntax

## Budget

~24 files. This is a large mechanical task (translation only, no architecture changes).

## Files to Translate

### Skills (6 files)

1. `skills/compress/SKILL.md` — Currently in Portuguese. Translate:
   - Frontmatter `description` field
   - All section headers (e.g., "Visao Geral" → "Overview", "Fase N" → "Phase N")
   - All instructions, rules, error messages, report templates
   - Critical rules table
   - Code comments in Portuguese
   - Keep code/bash commands as-is (only translate surrounding comments/instructions)

2. `skills/preserve/SKILL.md` — Same approach as compress

3. `skills/query/SKILL.md` — Same approach as compress

4. `skills/setup/SKILL.md` — **Already in English.** Verify and fix any remaining pt-BR fragments. Key areas to check:
   - Person template section has "Time", "Pontos Focais", "Assuntos Ativos" — translate to "Team", "Focal Points", "Active Topics"

5. `skills/sync/SKILL.md` — Same approach as compress. Has 3 modes (Sources, People, GitHub). The People mode uses old Portuguese field names (`tipo`, `nome`, `cargo`, etc.) — translate those to English equivalents (`type`, `name`, `role`)

6. `skills/teach/SKILL.md` — Same approach as compress

### Templates (7 files)

Each template has HTML comments in Portuguese and section headers. Translate:
- HTML comments (`<!-- Papel Zettelkasten: ... -->`, `<!-- Links no corpo... -->`, etc.)
- Section headers (e.g., "Contexto" → "Context", "Participantes" → "Participants")
- Placeholder descriptions in Portuguese
- Keep YAML keys in English (already are)
- Keep wikilink patterns as-is

Files:
1. `templates/actors/_template.md`
2. `templates/discussions/_template.md` — Sections: "Contexto", "Participantes", "Atores Discutidos", "Conclusoes", "Itens de Acao", "Projetos Relacionados", "Topicos Relacionados"
3. `templates/fleeting/_template.md` — Sections: "Conteudo", "Conexoes Possiveis", "Contexto de Captura"
4. `templates/people/_template.md` — Sections: "Time", "Pontos Focais", "Assuntos Ativos"
5. `templates/projects/_template.md` — Has Portuguese in Dataview queries, status convention note, "Prazo", "Responsavel"
6. `templates/teams/_template.md`
7. `templates/topics/_template.md`

### Entity Definitions (9 files)

These are fully in Portuguese. Each file follows the same structure:
- "O que e" → "What it is"
- "Quando criar" → "When to create"
- "Quando NAO criar" → "When NOT to create"
- "Como distinguir de outros tipos" → "How to distinguish from other types"
- "Campos obrigatorios" → "Required fields"
- "Papel Zettelkasten" → "Zettelkasten Role"
- "Exemplos" → "Examples"

Files:
1. `entities/actor.md`
2. `entities/discussion.md`
3. `entities/fleeting.md`
4. `entities/knowledge-node.md`
5. `entities/person.md`
6. `entities/project.md`
7. `entities/sources-field.md`
8. `entities/team.md`
9. `entities/topic.md`

### Documentation (2 files)

1. `CLAUDE.md` — Translate:
   - Git convention: `<type>` values (`pessoa` → `person`, `time` → `team`, `ator` → `actor`, `assunto` → `topic`, `discussao` → `discussion`, `projeto` → `project`, `nota` → `note`)
   - Git convention: `<verb>` values (`cria` → `creates`, `atualiza` → `updates`, `vincula` → `links`, `comprime` → `compresses`)
   - Git convention: `<source>` values (`memoria` → `memory`, `manual` → `manual`, etc.)
   - The `[fonte: ...]` pattern → `[source: ...]`
   - Scope values with Portuguese: `lgpd (fintech)` → `lgpd (fintech)`, `saude` → `health`, `Europa` → `Europe`
   - Writing Rules Language section: change from "Portuguese (pt-BR) for all content" to "English (en-US) for all content" (or make it configurable)
   - Frontmatter values example: change from pt-BR to en-US
   - Any remaining Portuguese scattered in the doc

2. `README.md` — Update:
   - Writing Rules section: change language default to English
   - Fix any remaining Portuguese references

## Directional Guidance

### Translation Conventions

- Use clear, direct English. Prefer active voice.
- Match the existing tone: instructional, concise, imperative for agent instructions.
- For the git convention, use English types but keep the `vault()` prefix format:
  ```
  vault(actor): updates billing-api [source: github]
  vault: teaches roadmap-26q1, creates 7 topics [source: confluence]
  vault: compress 25 entities across 8 clusters [source: compress]
  ```
- For report templates in skills, translate table headers and labels.
- For entity field descriptions, keep them concise (one line per field).
- Example content in entity definitions should use English names and scenarios (keep the structure, translate the narrative).

### Key Term Mappings

| Portuguese | English |
|---|---|
| Visao Geral | Overview |
| Fase N | Phase N |
| Regras criticas | Critical Rules |
| Relatorio | Report |
| Proposta | Proposal |
| Confirma a execucao? | Confirm execution? |
| Entidades a criar | Entities to create |
| Entidades a atualizar | Entities to update |
| Vinculacoes bidirecionais | Bidirectional links |
| Fontes consultadas | Sources consulted |
| Avisos | Warnings |
| Sugestoes | Suggestions |
| Conteudo consolidado em | Content consolidated in |
| Nenhuma entidade encontrada | No entities found |
| pessoa | person |
| time | team |
| ator | actor |
| assunto | topic |
| discussao | discussion |
| projeto | project |
| nota | note |
| cria | creates |
| atualiza | updates |
| vincula | links |
| comprime | compresses |
| fonte | source |
| memoria | memory |

### Approach

1. Start with entity definitions (they're referenced by skills)
2. Then templates (they're referenced by entity definitions)
3. Then skills (they reference entities and templates)
4. Finally documentation (CLAUDE.md, README.md)

For each file:
1. Read the current content
2. Translate all Portuguese to English while preserving:
   - YAML structure and keys
   - Markdown formatting
   - Code blocks and bash commands
   - Wikilink syntax `[[...]]`
   - File paths and technical identifiers
3. Write the translated content back

## How to Run/Test

No test runner — this is a markdown-only project. To validate:

1. After translating, grep for common Portuguese words to catch stragglers:
   ```bash
   grep -ri "quando\|nao\|entidade\|criacao\|atualizacao\|relatorio\|proposta\|obrigatorio" entities/ templates/ skills/ CLAUDE.md README.md
   ```

2. Verify YAML frontmatter is still valid in all files:
   ```bash
   for f in $(find . -name "*.md" -not -path "./.vibeflow/*"); do
     head -1 "$f" | grep -q "^---" && echo "OK: $f" || echo "WARN: $f"
   done
   ```

3. Verify wikilinks are intact (not accidentally translated):
   ```bash
   grep -r "\[\[" entities/ templates/ skills/ | head -20
   ```

---

Generated by `/vibeflow:quick` on 2026-04-13.
