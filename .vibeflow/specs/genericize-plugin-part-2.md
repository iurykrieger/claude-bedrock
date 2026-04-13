# Spec: Genericizar Plugin — Part 2: Templates + Root Docs

> Generated via /vibeflow:gen-spec on 2026-04-13
> PRD: `.vibeflow/prds/genericize-plugin.md`

## Objective

Aplicar o glossário canônico (da part 1) aos 7 templates e 2 arquivos raiz (`CLAUDE.md`, `README.md`), genericizando domínios, exemplos, e tabelas de tags.

## Context

Os templates contêm exemplos inline em comentários HTML e campos de frontmatter. `CLAUDE.md` contém a tabela de tags com domínios Stone e exemplos de wikilinks/commits. `README.md` tem uma menção a `domain/acquiring`. Todos precisam ser atualizados para usar os nomes genéricos definidos no glossário.

Mudanças de maior impacto nesta part:
- **Tabela `domain/*` em `CLAUDE.md`** — Substituir domínios Stone por genéricos, manter a tabela como "exemplos extensíveis"
- **Tabela `scope/*` em `CLAUDE.md`** — Adicionar exemplos de outras áreas além de fintech (`hipaa`, `gdpr`, `soc2`)
- **Exemplos de commit em `CLAUDE.md`** — Trocar `payment-card-api` por nome genérico

## Definition of Done

1. [ ] **7 templates atualizados** — Todos os arquivos em `templates/` usam nomes genéricos do glossário
2. [ ] **CLAUDE.md atualizado** — Tabela de domínios usa exemplos genéricos, tabela de scope tem exemplos multi-área, exemplos de wikilinks e commits usam nomes genéricos
3. [ ] **README.md atualizado** — Zero referências Stone
4. [ ] **Zero matches** — `grep -ri "stone\|pagarme\|pagar.me\|allstone\|stone-payments\|acquiring\|boleto" templates/ CLAUDE.md README.md` retorna vazio (exceto onde "acquiring" ou "boleto" sejam termos genéricos válidos em contexto técnico)
5. [ ] **Consistência com glossário** — Todos os nomes usados são idênticos aos definidos em `.vibeflow/specs/genericize-glossary.md`
6. [ ] **Tags domain/* atualizadas** — Tabela em CLAUDE.md e comentários em templates refletem os novos domínios genéricos

## Scope

### Templates (7 arquivos)

| Arquivo | Referências a substituir |
|---|---|
| `templates/people/_template.md` | `iury.krieger@stone.com.br`, `@iury.krieger`, `StoneCo`, `autobahn`, `payment-card-api` |
| `templates/teams/_template.md` | `Acquiring`, `Squad Acquiring`, domínios Stone no comentário de tags, `payment-card-api` |
| `templates/topics/_template.md` | `autobahn`, `Pagar.me`, `payment-card-api` |
| `templates/actors/_template.md` | Domínios Stone no comentário de tags |
| `templates/discussions/_template.md` | `leonardo-otero`, `autobahn` |
| `templates/projects/_template.md` | `autobahn` |
| `templates/fleeting/_template.md` | Verificar — pode não ter referências diretas |

### CLAUDE.md

- Tabela de entity types (linha 21-25): exemplos `payment-card-api.md`, `squad-acquiring.md`, `2026-04-02-daily-acquiring.md`
- Wikilinks (linha 49): `[[boleto-api]]`
- Tabela `domain/*` (linha 61): substituir domínios Stone inteiros por genéricos, adicionar frase "esta lista é extensível"
- Tabela `scope/*` (linha 62): manter `pci`, `sox`, `lgpd` como exemplo fintech, adicionar `hipaa` (saúde), `gdpr` (GDPR europeu), `soc2` (SaaS)
- Exemplo de commit (linha 130): `payment-card-api`
- Exemplo de wikilink semântico (linha 151): `payment-card-api`
- Don'ts (linha 165): `[[boleto-api]]`

### README.md

- Linha 63: `domain/acquiring` → domínio genérico

## Anti-scope

- Não alterar entities/ ou skills/ (parts 1 e 3)
- Não alterar a estrutura do CLAUDE.md — seções, regras de escrita, workflow git permanecem
- Não alterar plugin.json
- Não mudar o idioma padrão de pt-BR
- Não adicionar funcionalidade de `/init`

## Technical Decisions

1. **Domínios genéricos na tabela** — Usar domínios que qualquer empresa tech poderia ter: `payments`, `notifications`, `checkout`, `orders`, `integrations`, `finance`, `compliance`, `marketplace`, `internal-tools`, mais os já genéricos (`core`, `data`, `infra`, `platform`, `security`). Trade-off: perde a especificidade fintech, mas ganha universalidade.
2. **Scope como "categorias de uso"** — A tabela de `scope/*` passa a ser apresentada como exemplos de diferentes indústrias, não uma lista fechada. Inclui: `pci`/`sox`/`lgpd` (fintech), `hipaa` (saúde), `gdpr` (Europa), `soc2` (SaaS). Trade-off: mais exemplos na tabela, mas demonstra flexibilidade.
3. **Frase "extensível" explícita** — Adicionar nota nas tabelas de domínio e scope indicando que são exemplos, não uma lista fechada. Deixa claro que o usuário pode criar novos.

## Applicable Patterns

Nenhum — projeto não tem `.vibeflow/patterns/`.

## Risks

1. **Domínios nos templates desalinhados** — Comentários em `_template.md` listam domínios disponíveis para tags. Se a tabela em `CLAUDE.md` mudar e os templates não acompanharem, fica inconsistente. Mitigação: atualizar ambos na mesma part.
2. **CLAUDE.md é lido por AI agents** — Qualquer erro na tabela de tags afeta o comportamento de todas as skills. Mitigação: DoD inclui grep de validação.

## Dependencies

- `.vibeflow/specs/genericize-plugin-part-1.md` — Glossário deve existir antes de começar esta part.

## Files

- `templates/people/_template.md`
- `templates/teams/_template.md`
- `templates/topics/_template.md`
- `templates/actors/_template.md`
- `templates/discussions/_template.md`
- `templates/projects/_template.md`
- `templates/fleeting/_template.md`
- `CLAUDE.md`
- `README.md`
