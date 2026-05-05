# Prompt Pack — Rename `/bedrock:teach` to `/bedrock:learn`

> You are only seeing this prompt; there is no context outside it.

---

## 1. Objective and Definition of Done

**Objective:** Renomear o comando `/bedrock:teach` para `/bedrock:learn` em todas as referências do plugin (skills, docs, site), mantendo `/bedrock:teach` como alias de retrocompatibilidade que delega ao novo skill.

**Definition of Done:**
- [ ] Diretório `skills/learn/` existe com `SKILL.md` completo (conteúdo do antigo `teach` com nome atualizado)
- [ ] `skills/teach/SKILL.md` é um wrapper minimalista que delega a `/bedrock:learn` com mensagem de deprecação
- [ ] Todas as referências a `/bedrock:teach` em outros skills (`ask`, `healthcheck`, `setup`, `sync`, `preserve`, `confluence-to-markdown`, `gdoc-to-markdown`) apontam para `/bedrock:learn`
- [ ] `CLAUDE.md`, `README.md`, `entities/fleeting.md`, `entities/sources-field.md` atualizados
- [ ] `index.html` e os arquivos de site (`site/data/skills.ts`, `site/components/how-it-works.tsx`) atualizados

---

## 2. Anti-scope

- **NÃO** deletar `skills/teach/` — deve continuar existindo como backward-compat wrapper
- **NÃO** alterar a lógica do skill, apenas renomear referências
- **NÃO** modificar templates em `templates/`
- **NÃO** alterar `skills/compress/`, `skills/vaults/`, nem qualquer outro skill que não referencie `teach`
- **NÃO** criar documentação extra — o scope é apenas renomear

---

## 3. Budget

> **Aviso:** Esta tarefa afeta ~16 arquivos, o que excede o budget padrão do `/vibeflow:quick` (≤4 arquivos). O conjunto de mudanças é mecânico (find-and-replace + 1 novo arquivo + 1 wrapper), então prossiga com cautela e valide cada arquivo.

---

## 4. Patterns to Follow

**Skill naming convention** (de `conventions.md`):
- Skill names: single lowercase word matching directory name
- Skill file: `skills/<name>/SKILL.md`
- Heading: `# /bedrock:<name>`

**Wrapper de backward-compat pattern** (inferido da arquitetura):
O wrapper deve usar o frontmatter YAML completo mas com `description` indicando deprecação, e o corpo deve apenas informar o usuário e invocar o skill novo via `Skill` tool.

---

## 5. Where to Work

### Novo arquivo a criar

**`skills/learn/SKILL.md`** — copiar `skills/teach/SKILL.md` e substituir:
- Frontmatter: `name: teach` → `name: learn`
- Frontmatter `description`: atualizar triggers (`"bedrock learn"`, `"bedrock-learn"`, `"learn"`, `/bedrock:learn"`, etc.)
- Heading: `# /bedrock:teach` → `# /bedrock:learn`
- Todas as ocorrências internas de `/bedrock:teach` → `/bedrock:learn`
- Todas as ocorrências de `/teach` (sem prefixo) → `/learn`

### Arquivo a transformar em wrapper

**`skills/teach/SKILL.md`** (atual: ~30+ linhas, conteúdo completo) — substituir por wrapper mínimo:

```markdown
---
name: teach
description: >
  [DEPRECATED] Alias de retrocompatibilidade para /bedrock:learn.
  Use /bedrock:learn para ingerir fontes externas no vault.
  Trigger: "bedrock teach", "/bedrock:teach"
user_invocable: true
allowed-tools: Skill
---

# /bedrock:teach — Alias de retrocompatibilidade

> [!warning] Deprecated
> `/bedrock:teach` foi renomeado para `/bedrock:learn`.
> Este alias continuará funcionando, mas use `/bedrock:learn` em novos fluxos.

Delegando para `/bedrock:learn`...
```

O wrapper deve, após exibir o aviso, invocar `/bedrock:learn` via `Skill` tool passando todos os argumentos recebidos.

### Arquivos de skills com referências a atualizar

Substituição: `/bedrock:teach` → `/bedrock:learn`, `/teach` (quando referência ao skill) → `/learn`

| Arquivo | Ocorrências |
|---|---|
| `skills/ask/SKILL.md` | ~12 ocorrências de `/bedrock:teach` e `/teach` |
| `skills/healthcheck/SKILL.md` | 4 ocorrências de `/bedrock:teach` |
| `skills/setup/SKILL.md` | ~8 ocorrências de `/bedrock:teach` e `/teach` |
| `skills/sync/SKILL.md` | 1 ocorrência de `/bedrock:teach` |
| `skills/preserve/SKILL.md` | ~7 ocorrências de `/bedrock:teach` e `/teach` |
| `skills/confluence-to-markdown/SKILL.md` | 3 ocorrências de `/bedrock:teach` |
| `skills/gdoc-to-markdown/SKILL.md` | 3 ocorrências de `/bedrock:teach` |

### Arquivos de documentação

| Arquivo | O que mudar |
|---|---|
| `CLAUDE.md` (linha 32 e 110) | `/bedrock:teach` → `/bedrock:learn` na tabela de skills |
| `README.md` (linhas 69, 103, 117, 118, 120, 122) | `/bedrock:teach` → `/bedrock:learn` |
| `entities/fleeting.md` (linhas 28, 62, 75) | `/teach` → `/learn` |
| `entities/sources-field.md` (linha 37) | `/teach` → `/learn` |

### Arquivos do site

**`site/data/skills.ts`** (linhas 23-30):
```ts
// ANTES
id: "teach",
name: "teach",
command: "/bedrock:teach",
videoPath: "/videos/teach.mp4",

// DEPOIS
id: "learn",
name: "learn",
command: "/bedrock:learn",
videoPath: "/videos/learn.mp4",  // ou manter teach.mp4 se o vídeo não for renomeado
```

**`site/components/how-it-works.tsx`** (linhas 12-13):
```tsx
// ANTES
command: "/bedrock:teach",
videoPath: "/videos/teach.mp4",

// DEPOIS
command: "/bedrock:learn",
videoPath: "/videos/learn.mp4",  // ou manter teach.mp4 se vídeo não for renomeado
```

**`index.html`** — 7 ocorrências:
- `step-name`: `teach` → `learn`
- `skill-name`: `/bedrock:teach` → `/bedrock:learn`
- Chaves i18n `wf_teach` e `sk_teach` → `wf_learn` e `sk_learn` (em todas as línguas no bloco JS)

---

## 6. Directional Guidance

1. **Comece pelo novo skill**: crie `skills/learn/SKILL.md` a partir do conteúdo atual de `skills/teach/SKILL.md`, fazendo as substituições de nome antes de qualquer outra mudança.
2. **Transforme o teach em wrapper**: substitua o conteúdo de `skills/teach/SKILL.md` pelo wrapper mínimo. O wrapper deve invocar `bedrock:learn` via `Skill` tool sem re-processar argumentos.
3. **Atualize os outros skills** em ordem: `ask` → `preserve` → `setup` → `healthcheck` → `sync` → `confluence-to-markdown` → `gdoc-to-markdown`.
4. **Atualize docs**: `CLAUDE.md`, `README.md`, `entities/`.
5. **Atualize o site** por último: `index.html`, depois os componentes Next.js.
6. **Não renomeie o vídeo** `public/videos/teach.mp4` sem instrução explícita — apenas atualize a referência no código caso o arquivo seja renomeado.

---

## 7. How to Run/Test

Este projeto não tem test runner de código (é um plugin de Markdown + Next.js).

**Validação manual obrigatória:**

```bash
# 1. Verificar que o novo skill existe
ls skills/learn/SKILL.md

# 2. Verificar que teach ainda existe como wrapper
ls skills/teach/SKILL.md

# 3. Verificar que não restaram referências a /bedrock:teach fora do wrapper
grep -rn "bedrock:teach" skills/ --include="*.md" | grep -v "skills/teach/SKILL.md"
# Esperado: nenhuma saída (ou apenas referência histórica no wrapper)

grep -rn "bedrock:teach" CLAUDE.md README.md entities/ index.html site/
# Esperado: nenhuma saída

# 4. Verificar que /bedrock:learn aparece nas referências corretas
grep -rn "bedrock:learn" skills/ask/SKILL.md | wc -l
# Esperado: >= 10

# 5. Validar o site Next.js (se disponível)
cd site && npm run build
```
