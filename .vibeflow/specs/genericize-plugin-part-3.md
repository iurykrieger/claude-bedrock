# Spec: Genericizar Plugin — Part 3: Skills + Validação Final

> Generated via /vibeflow:gen-spec on 2026-04-13
> PRD: `.vibeflow/prds/genericize-plugin.md`

## Objective

Aplicar o glossário canônico (da part 1) a todos os 5 skill files e executar validação final cross-repo, garantindo zero referências Stone em todo o plugin.

## Context

Os skills são os arquivos mais longos e complexos do plugin. Contêm exemplos de comandos, tabelas de output, templates de commit, e instruções de matching — todos com referências Stone hardcoded. Além disso, dois skills (`teach` e `sync`) contêm URLs de GitHub e Atlassian da Stone nos exemplos de uso.

Após esta part, o plugin deve estar 100% livre de referências Stone.

## Definition of Done

1. [ ] **5 skill files atualizados** — `query/SKILL.md`, `teach/SKILL.md`, `preserve/SKILL.md`, `sync/SKILL.md`, `compress/SKILL.md` usam nomes genéricos do glossário
2. [ ] **URLs genéricas** — Nenhuma URL `allstone.atlassian.net` ou `github.com/stone-payments` nos skills
3. [ ] **Exemplos de matching preservados** — Os exemplos de entity matching e disambiguation em `preserve` e `teach` continuam didáticos com nomes genéricos
4. [ ] **Validação final cross-repo** — `grep -ri "stone\|pagarme\|pagar.me\|allstone\|stone-payments" entities/ templates/ skills/ CLAUDE.md README.md` retorna vazio
5. [ ] **Consistência com glossário** — Todos os nomes usados são idênticos aos de `.vibeflow/specs/genericize-glossary.md`
6. [ ] **Nomes de pessoas genéricos** — Nenhum nome de colaborador Stone (Iury, Leonardo, Giovanna, Jaderson, Fulano, Ciclano, Beltrano) presente nos skills; substituídos por nomes genéricos do glossário

## Scope

### Skills (5 arquivos)

| Arquivo | Referências a substituir | Complexidade |
|---|---|---|
| `skills/teach/SKILL.md` | `stone-payments/payment-card-api` (URL exemplo), `acquiring` (diretório de busca), `"stone"` (lista de stop-words), `payment-card-api` (tabelas e exemplos) | Alta — exemplos longos com tabelas |
| `skills/sync/SKILL.md` | `allstone.atlassian.net`, `stone-payments/pca`, `payment-card-api`, `pix-receiver`, `squad-acquiring`, `squad-boleto`, `boleto-api`, `"stone"` (stop-word), `fulano`/`ciclano`/`beltrano` | Alta — exemplos de sync com múltiplas fontes |
| `skills/preserve/SKILL.md` | `payment-card-api`, `PCA` (alias), `squad-acquiring`, `autobahn`, `payment-new-api` | Média — exemplos de matching e linking |
| `skills/query/SKILL.md` | `payment-card-api`, `squad-acquiring`, `acquiring`, `boleto`, `charge`, `pix`, `cards` (lista de domínios) | Média — exemplos de busca |
| `skills/compress/SKILL.md` | `payment-card-api` | Baixa — uma referência |

### Detalhes por skill

**teach/SKILL.md:**
- Exemplo de URL GitHub (linha ~59): trocar `stone-payments/payment-card-api` por `acme-corp/billing-api`
- Busca local de repos (linha ~81): trocar `acquiring/` por diretório genérico
- Stop-words (linha ~395): manter `"stone"` na lista OU trocar por outro exemplo de palavra genérica a não matchar — decisão: **remover "stone" da lista de stop-words**, substituir por outro exemplo genérico como `"company"`
- Tabelas de output (linhas ~510-617): trocar `payment-card-api` por `billing-api`
- Wikilinks em metadata (linha ~571): trocar `[[payment-card-api]]` por `[[billing-api]]`

**sync/SKILL.md:**
- URLs de fonte (linhas ~107-112): trocar `allstone.atlassian.net` e `stone-payments/pca`
- Filenames de actor (linha ~199): trocar `payment-card-api`
- Exemplos de matching (linhas ~211-213): trocar exemplos, trocar stop-word `"stone"` → `"company"`
- Tabelas de output (linhas ~253-289): trocar `pix-receiver` → `webhook-receiver`
- Report table (linha ~357): trocar `stone-payments-pca`
- URLs de repo (linha ~409): trocar `stone-payments/payment-card-api`
- Wikilinks de squad (linhas ~410-415): trocar `[[squad-acquiring]]` → equivalente genérico
- Contagem por squad (linha ~451): trocar `squad-acquiring`, `squad-boleto`
- Pontos focais (linhas ~506-510): trocar `[[payment-card-api]]`, `[[boleto-api]]`
- Tabela de squads (linhas ~568-569): trocar squads e nomes de pessoas

**preserve/SKILL.md:**
- Exemplos de matching (linhas ~176-179): trocar `payment-card-api`, `PCA`
- Tabelas de plano (linhas ~226-237): trocar `payment-new-api`, `squad-acquiring`, `payment-card-api`
- Exemplos semânticos (linhas ~323-325): trocar `autobahn`, `payment-card-api`
- Resumo final (linhas ~494-500): trocar mesmas referências

**query/SKILL.md:**
- Exemplos de busca (linhas ~51-56): trocar nomes de entidades e lista de domínios
- Exemplos de perguntas (linhas ~141, ~272-273): trocar domínios

**compress/SKILL.md:**
- Uma referência (linha ~270): trocar `payment-card-api`

## Anti-scope

- Não alterar entities/ ou templates/ (parts 1 e 2)
- Não alterar a lógica das skills — apenas exemplos, URLs, e textos descritivos
- Não alterar instruções de matching, regras de stop-words, ou algoritmos
- Não adicionar novas funcionalidades às skills

## Technical Decisions

1. **Stop-word "stone" → "company"** — A lista de stop-words em `teach` e `sync` inclui "stone" como exemplo de palavra genérica a não matchar. Trocar por "company" que serve o mesmo propósito didático. Trade-off: nenhum — "company" é igualmente genérico.
2. **Alias "PCA" → alias genérico** — O exemplo de matching por alias usa "PCA" (Payment Card API). Trocar por uma sigla que faça sentido para o novo nome (ex: se `billing-api`, alias poderia ser "BA" ou "BillingAPI"). Trade-off: sigla de 2 letras é menos didática, usar "BillingAPI" como alias.
3. **Validação final agressiva** — O grep final inclui variantes case-insensitive e cobre TODO o repo (exceto `.git/` e `.vibeflow/`). Isso pega referências que poderiam ter escapado nas parts anteriores.

## Applicable Patterns

Nenhum — projeto não tem `.vibeflow/patterns/`.

## Risks

1. **Skills são documentação executável** — AI agents leem os skills como instruções. Se um exemplo ficar inconsistente (nome no texto diferente do nome na tabela), o agent pode se confundir. Mitigação: DoD exige consistência com glossário.
2. **Stop-words afetam matching** — Trocar a stop-word de exemplo pode parecer inofensivo, mas se alguém copiar a lista literalmente, "company" como stop-word pode causar falsos negativos. Mitigação: o exemplo é didático, a lista real é definida pelo usuário.
3. **Volume de mudanças em sync/SKILL.md** — Este é o arquivo com mais referências (~20 matches). Risco de perder alguma. Mitigação: grep por arquivo individual após edição.

## Dependencies

- `.vibeflow/specs/genericize-plugin-part-1.md` — Glossário deve existir
- `.vibeflow/specs/genericize-plugin-part-2.md` — Templates e CLAUDE.md devem estar atualizados (para que a validação final cross-repo funcione)

## Files

- `skills/query/SKILL.md`
- `skills/teach/SKILL.md`
- `skills/preserve/SKILL.md`
- `skills/sync/SKILL.md`
- `skills/compress/SKILL.md`
