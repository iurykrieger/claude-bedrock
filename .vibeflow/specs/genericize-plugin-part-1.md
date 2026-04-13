# Spec: Genericizar Plugin — Part 1: Glossário + Entity Definitions

> Generated via /vibeflow:gen-spec on 2026-04-13
> PRD: `.vibeflow/prds/genericize-plugin.md`

## Objective

Definir um glossário canônico de substituições (Stone → genérico) e aplicá-lo a todos os 9 arquivos em `entities/`, eliminando referências à StoneCo sem perder a qualidade didática dos exemplos.

## Context

Os entity definitions em `entities/` são os arquivos mais densos em referências Stone — contêm exemplos de classificação, disambiguation, e linking que mencionam sistemas (`payment-card-api`, `autobahn`, `boleto-api`, `charge-probe`, `decryptor`), pessoas (`Iury Krieger`, `Leonardo Bittencourt`, `Giovanna`, `Jaderson Gomes`), squads (`Acquiring`, `Boleto`), subsidiárias (`Pagar.me`, `Ton`), URLs (`allstone.atlassian.net`, `stone-payments/*`), e emails (`@stone.com.br`).

O glossário definido aqui será a referência canônica para as parts 2 e 3.

## Definition of Done

1. [ ] **Glossário criado** — Arquivo `.vibeflow/specs/genericize-glossary.md` existe com mapeamento completo de: sistemas, pessoas, squads, domínios, URLs, emails, e subsidiárias
2. [ ] **9 entity files atualizados** — `actor.md`, `person.md`, `team.md`, `topic.md`, `discussion.md`, `project.md`, `fleeting.md`, `knowledge-node.md`, `sources-field.md` não contêm referências Stone
3. [ ] **Zero matches** — `grep -ri "stone\|pagarme\|pagar.me\|allstone\|stone-payments" entities/` retorna vazio
4. [ ] **Exemplos coerentes** — Wikilinks nos exemplos referenciam os mesmos nomes genéricos definidos no glossário (ex: se glossário mapeia `payment-card-api` → `billing-api`, todas as ocorrências em entities/ usam `billing-api`)
5. [ ] **Estrutura preservada** — Nenhuma seção, campo de frontmatter, ou regra de classificação foi alterada — apenas os exemplos/textos descritivos

## Scope

### Glossário de Substituições

Criar `.vibeflow/specs/genericize-glossary.md` com a tabela de mapeamento. O glossário deve ser autodescritivo — cada entrada genérica deve fazer sentido isoladamente, sem parecer que veio de uma empresa específica. Diretrizes:

**Sistemas (actors):**
- Usar nomes de sistemas genéricos que qualquer empresa de tech poderia ter
- Manter variedade de stacks nos exemplos (não trocar tudo para o mesmo tipo de sistema)
- Exemplos de mapeamento sugeridos (confirmar no glossário):
  - `payment-card-api` → `billing-api` (API de cobrança)
  - `boleto-api` → `notification-service` (serviço de notificações)
  - `autobahn` → `legacy-gateway` (gateway legado em deprecação)
  - `charge-probe` → `health-checker` (probe de saúde)
  - `decryptor` → `crypto-service` (serviço de criptografia)
  - `pix-receiver` → `webhook-receiver` (receptor de webhooks)
  - `brand-retry-blocker` → `rate-limiter` (limitador de taxa)
  - `boleto-recovery-consumer` → `retry-consumer` (consumer de retry)
  - `charge-api` → `orders-api` (API de pedidos)
  - `probe-consumer` → `metrics-collector` (coletor de métricas)
  - `ProbeAPI` → `MonitorAPI` (API de monitoramento legada)

**Pessoas:**
- Usar nomes fictícios e genéricos
- Mapeamento sugerido:
  - `Iury Krieger` / `iury.krieger` → `alice.smith` / `Alice Smith`
  - `Leonardo Bittencourt` / `leonardo-otero` → `bob.jones` / `Bob Jones`
  - `Giovanna` → `Carol`
  - `Jaderson Gomes` / `jadersgomes` → `dave.wilson` / `davewilson`
  - `Fulano` → `Alice` (placeholder genérico)
  - `Ciclano` → `Bob`
  - `Beltrano` → `Carol`

**Squads/Times:**
- `Squad Acquiring` → `Squad Payments` ou `Squad Backend`
- `Squad Boleto` → `Squad Notifications`
- `Squad Charge` → `Squad Orders`

**Domínios (tags):**
- `acquiring` → `payments`
- `boleto` → `notifications`
- `cards` → `checkout`
- `charge` → `orders`
- `pix` → `integrations`
- `banking` → `finance`
- `insurance` → `compliance`
- `marketplace` → `marketplace` (já genérico)
- `orders` → `orders` (já genérico)
- `staffs` → `internal-tools`
- Manter: `core`, `data`, `infra`, `platform`, `security` (já genéricos)

**URLs e Orgs:**
- `stone-payments` → `acme-corp` (org GitHub genérica)
- `allstone.atlassian.net` → `mycompany.atlassian.net`
- `@stone.com.br` → `@company.com`
- `stone.com.br` → `company.com`

**Subsidiárias:**
- `StoneCo (Stone, Pagar.me, Ton)` → remover completamente, sem substituição

### Entity Files

Aplicar o glossário a cada arquivo, preservando a estrutura e qualidade didática dos exemplos.

## Anti-scope

- Não alterar templates/, skills/, CLAUDE.md, ou README.md (parts 2 e 3)
- Não alterar a estrutura dos entity files — seções, campos, regras de classificação permanecem intactas
- Não alterar a lógica de matching ou regras de disambiguation — apenas os exemplos
- Não criar novos entity types

## Technical Decisions

1. **Glossário como artefato separado** — Em vez de definir substituições inline, criar um arquivo de referência que as parts 2 e 3 seguem. Isso garante consistência cross-file. Trade-off: um arquivo extra, mas elimina risco de inconsistência.
2. **Nomes genéricos com personalidade** — Usar `billing-api`, `notification-service` em vez de `service-a`, `service-b`. Exemplos genéricos mas realistas são mais didáticos. Trade-off: mais trabalho para escolher nomes, mas resultado final é mais útil.
3. **Grep como validação** — A validação é textual: grep case-insensitive por padrões Stone. Sem build ou testes para rodar.

## Applicable Patterns

Nenhum — projeto não tem `.vibeflow/patterns/`.

## Risks

1. **Inconsistência no glossário** — Se um nome genérico é ambíguo ou se repete, exemplos perdem clareza. Mitigação: revisar o glossário antes de aplicar, garantir que cada nome genérico é único e descritivo.
2. **Exemplos perdem contexto didático** — Exemplos Stone foram pensados para contar uma "história" coerente (migração do autobahn, squad Boleto, etc). Nomes genéricos podem quebrar essa narrativa. Mitigação: manter a mesma narrativa com nomes diferentes (ex: "migração do legacy-gateway para billing-api").
3. **Falso negativo no grep** — Referências que não usam os termos exatos (ex: "PCA" como sigla de payment-card-api). Mitigação: verificar aliases e siglas no glossário.

## Dependencies

Nenhuma — esta é a primeira parte.

## Files

- `.vibeflow/specs/genericize-glossary.md` (criar)
- `entities/actor.md`
- `entities/person.md`
- `entities/team.md`
- `entities/topic.md`
- `entities/discussion.md`
- `entities/project.md`
- `entities/fleeting.md`
- `entities/knowledge-node.md`
- `entities/sources-field.md`
