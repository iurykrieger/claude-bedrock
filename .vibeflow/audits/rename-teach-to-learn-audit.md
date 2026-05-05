# Audit Report: rename-teach-to-learn

**Verdict: PASS**

**Date:** 2026-05-05
**Source:** Prompt pack `.vibeflow/prompt-packs/rename-teach-to-learn.md`

---

## DoD Checklist

- [x] `skills/learn/SKILL.md` criado com conteúdo completo — `skills/learn/SKILL.md` (549 linhas), frontmatter `name: learn`, heading `# /bedrock:learn — External Source Ingestion into the Second Brain`, `user_invocable: true`, todas as seções obrigatórias presentes (Plugin Paths, Overview, fases numeradas, Critical Rules).
- [x] `skills/teach/SKILL.md` é wrapper minimalista que delega a `/bedrock:learn` — 19 linhas, aviso `[!warning] Deprecated`, instrução explícita para invocar `bedrock:learn` via Skill tool com todos os argumentos.
- [x] Referências a `/bedrock:teach` em outros skills atualizadas — grep retornou zero ocorrências em `skills/ask/`, `skills/healthcheck/`, `skills/setup/`, `skills/sync/`, `skills/preserve/`, `skills/confluence-to-markdown/`, `skills/gdoc-to-markdown/`. `skills/ask/SKILL.md` contém 12 ocorrências de `/bedrock:learn`.
- [x] `CLAUDE.md`, `README.md`, `entities/fleeting.md`, `entities/sources-field.md` atualizados — grep retornou zero ocorrências de `bedrock:teach` e `/teach` nesses arquivos.
- [x] Site atualizado (`index.html`, `site/data/skills.ts`, `site/components/how-it-works.tsx`) — `id: "learn"`, `command: "/bedrock:learn"` em skills.ts; `/bedrock:learn` em how-it-works.tsx e index.html; chaves i18n `wf_learn`/`sk_learn` em ambas as línguas no index.html.

---

## Pattern Compliance

- [x] **Skill naming convention** — `skills/learn/SKILL.md` segue `skills/<name>/SKILL.md`; `name: learn` no frontmatter; heading `# /bedrock:learn`. Conforme `conventions.md`.
- [x] **Skill structure convention** — `learn/SKILL.md` tem frontmatter YAML completo, heading `# /bedrock:<name>`, seção `## Plugin Paths`, `## Overview`, fases numeradas, `## Critical Rules` no final. Conforme `conventions.md`.
- [x] **Backward-compat wrapper pattern** — `skills/teach/SKILL.md` tem frontmatter com `description` indicando deprecação, `allowed-tools: Skill`, aviso `[!warning]`, e instrução de delegação. Adequado ao padrão inferido da arquitetura.

---

## Convention Violations

Nenhuma violação encontrada.

---

## Tests

- **Stack:** Next.js (site) + plugin de Markdown (sem runner de testes)
- **Build Next.js:** `npm run build` → **PASS** (compiled successfully, 4/4 static pages, TypeScript clean)
- **Validação grep:** zero referências residuais de `/bedrock:teach` fora de `skills/teach/SKILL.md`

---

## Notes

- O arquivo de vídeo `site/public/videos/teach.mp4` **não foi renomeado** (conforme anti-scope do prompt pack — nenhuma instrução explícita para renomear). O `videoPath` nos dois componentes do site continua apontando para `/videos/teach.mp4`. Se o vídeo for renomeado futuramente para `learn.mp4`, atualizar `site/data/skills.ts:30` e `site/components/how-it-works.tsx:13`.
- A variável interna `TEACH_TMP` foi renomeada para `LEARN_TMP` no `skills/learn/SKILL.md` (31 ocorrências), mantendo consistência com o novo nome.

---

## Overall: READY TO SHIP
