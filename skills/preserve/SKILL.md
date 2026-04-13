---
name: preserve
description: >
  Ponto unico de escrita no vault. Centraliza deteccao de entidades, matching textual,
  criacao/atualizacao de entidades e vinculacao bidirecional. Aceita input estruturado
  (lista de entidades) ou input livre (texto, meeting notes, contexto de sessao).
  Use quando: "bedrock preserve", "bedrock-preserve", "salvar no vault", "registrar no vault", "/bedrock:preserve",
  ou quando outro skill (ex: /bedrock:teach) precisar persistir entidades no vault.
user_invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, mcp__plugin_github_github__*, mcp__plugin_atlassian_atlassian__*
---

# /bedrock:preserve — Ponto Unico de Escrita no Vault

## Plugin Paths

Entity definitions e templates estao no diretorio do plugin, nao na raiz do vault.
Use o "Base directory for this skill" informado na invocacao para resolver os paths:

- Entity definitions: `<base_dir>/../../entities/`
- Templates: `<base_dir>/../../templates/{type}/_template.md`
- CLAUDE.md do plugin: `<base_dir>/../../CLAUDE.md` (ja injetado automaticamente no contexto)

Onde `<base_dir>` e o path informado em "Base directory for this skill".

---

## Visao Geral

Esta skill centraliza TODA a logica de escrita no vault. Ela recebe input (estruturado ou livre),
identifica entidades, correlaciona com o vault existente, propoe mudancas ao usuario, e executa
apos confirmacao. E o unico caminho para criar ou atualizar entidades no vault (exceto `/sync-people`
que trata people/teams via GitHub API).

**Voce e um agente de execucao.** Siga as fases abaixo na ordem, sem pular etapas.

---

## Fase 0 — Sincronizar o Vault

Execute:
```bash
git pull --rebase origin main
```

Se o pull falhar:
- Sem remote configurado: avisar "Nenhum remote configurado. Trabalhando localmente." e prosseguir.
- Conflito no pull: `git rebase --abort` e avisar o usuario. NAO prosseguir sem resolver.
- Caso contrario: prosseguir.

---

## Fase 1 — Parsear Input

O `/bedrock:preserve` aceita dois modos de input. Determine qual aplicar:

### 1.1 Input estruturado

Quando chamado por outra skill (ex: `/bedrock:teach`) ou quando o usuario fornece uma lista explicita.
O formato e uma lista de entidades, cada uma com:

```yaml
- type: actor | person | team | topic | discussion | project | fleeting | knowledge-node
  name: "nome canonico da entidade"
  action: create | update
  content: "conteudo a incluir no corpo da entidade"
  relations:
    actors: ["actor-slug-1", "actor-slug-2"]
    people: ["person-slug-1"]
    teams: ["team-slug-1"]
    topics: ["topic-slug-1"]
    discussions: ["discussion-slug-1"]
    projects: ["project-slug-1"]
    knowledge_nodes: ["node-slug-1"]
  source: "github | confluence | jira | session | manual | gdoc | csv | graphify"
  metadata: {}  # campos adicionais de frontmatter especificos do tipo
```

Se o input segue este formato (ou algo proximo): parsear diretamente e ir para Fase 2.

### 1.2 Input livre

Quando o usuario fornece texto natural, meeting notes, contexto de sessao, ou qualquer conteudo
nao-estruturado. Analise o texto e extraia:

1. **Entidades mencionadas** — identificar por nome, apelido ou referencia:
   - Pessoas: nomes no formato "Nome Sobrenome"
   - Atores: nomes de servicos, APIs, repositorios
   - Times: nomes de squads
   - Assuntos: temas de discussao, bugs, RFCs, features
   - Discussoes: reunioes, decisoes, debates
   - Projetos: iniciativas, migracoes, features cross-team

2. **Acao inferida** — para cada entidade:
   - Se a entidade ja existe no vault: `update`
   - Se a entidade nao existe: `create`

3. **Conteudo** — o que foi dito sobre cada entidade no input

4. **Relacoes** — inferir quais entidades se relacionam entre si com base no contexto

5. **Fonte** — inferir: `session` (conversa), `meeting-notes` (ata), `manual` (texto digitado)

Para classificar conteudo novo, consulte as entity definitions do plugin (ver secao "Plugin Paths") (carregadas na Fase 2.0):
- Secao "Quando criar" → criterios positivos para criar nova entidade
- Secao "Quando NAO criar" → criterios de exclusao
- Secao "Como distinguir de outros tipos" → desambiguacao

Converter o resultado para o formato estruturado da secao 1.1 e prosseguir.

### 1.3 Classificacao Zettelkasten

Antes de converter para formato estruturado, classificar cada entidade por papel Zettelkasten.
Consultar entity definitions do plugin (secao "Criterio de Completude") para determinar o tipo correto:

**Regra de classificacao:**
- Se o conteudo atende os criterios de completude de um tipo permanent (actor, person, team) → classificar como permanent
- Se o conteudo tem `graphify_node_id` e `actor` definidos → classificar como `knowledge-node` (extensao de permanent, sub-entidade de actor)
- Se o conteudo atende os criterios de completude de um tipo bridge (topic, discussion) → classificar como bridge
- Se o conteudo atende os criterios de completude de um tipo index (project) → classificar como index
- **Se o conteudo NAO atende os criterios de completude de nenhum tipo** → classificar como `fleeting`

**Heuristicas para fleeting:**
- Mencao vaga sem dados concretos (sem nome de repo, sem nome completo de pessoa, sem data, sem decisao)
- Ideia ou hipotese sem confirmacao ("parece que...", "talvez...", "alguem mencionou...")
- Fragmento de informacao sem contexto suficiente para ser auto-contido
- TODO generico sem responsavel ou prazo

**Na duvida, errar para o lado de fleeting** — e mais seguro capturar como fleeting e promover depois do que criar uma entidade permanente incompleta.

Se o input veio de outro skill (ex: `/bedrock:teach`) e ja inclui sugestao de classificacao (`type: fleeting`), respeitar a sugestao mas validar contra os criterios acima.

Se nenhum input foi fornecido: perguntar ao usuario "O que deseja preservar no vault? Forneca texto, meeting notes, ou uma lista de entidades."

---

## Fase 2 — Matching com Entidades Existentes

**Objetivo:** Correlacionar as entidades do input com o vault existente.

### 2.0 Ler entity definitions

Ler TODOS os arquivos de entity definitions do plugin (ver secao "Plugin Paths"):
`<base_dir>/../../entities/*.md`
Esses arquivos definem o que cada tipo de entidade e, quando criar, quando NAO criar, e como
distinguir entre tipos. Internalize essas definicoes — voce vai usa-las para classificar conteudo
novo (especialmente em modo livre, Fase 1.2).

### 2.1 Coletar entidades do vault

Listar todos os arquivos em cada diretorio de entidades (excluir `_template.md` e `_template_node.md`):

```
actors/*.md e actors/*/*.md (atores podem ser pastas: actors/<name>/<name>.md)
actors/*/nodes/*.md (knowledge-nodes dentro de atores)
people/*.md
teams/*.md
topics/*.md
discussions/*.md (se existir)
projects/*.md (se existir)
fleeting/*.md (se existir)
```

Para cada arquivo encontrado, extrair:
- `filename` (sem extensao) — identificador canonico
- `name` (ou `title`) do frontmatter — nome legivel
- `aliases` do frontmatter — nomes alternativos
- `graphify_node_id` do frontmatter — para knowledge-nodes (se presente)

### 2.2 Matching textual

Para cada entidade do input, verificar se ja existe no vault:

**Regras de match (em ordem de prioridade):**

1. **Match exato por filename** (case-insensitive): `billing-api` == `billing-api`
2. **Match por name/title field** (case-insensitive): `"Billing API"` encontra `billing-api.md`
3. **Match por aliases** (case-insensitive): `"BillingAPI"` encontra `billing-api.md` se alias contem "BillingAPI"
4. **Match por filename sem hifens** (case-insensitive): `billing-api` → `billingapi` encontra "BillingAPI"
5. **Match por graphify_node_id** (para knowledge-nodes): match exato por `graphify_node_id` no frontmatter. Este e o match mais confiavel para knowledge-nodes e tem prioridade sobre os demais quando presente.

**Regras de seguranca:**
- NAO fazer match por substrings de 3 letras ou menos (ex: "api" nao deve matchar tudo)
- Maximo 20 correlacoes por tipo de entidade
- Em caso de ambiguidade: registrar todos os candidatos e resolver na Fase 3 (proposta)

### 2.3 Classificar acoes

Para cada entidade do input:
- Se match encontrado no vault: marcar como `update` (atualizar entidade existente)
- Se nenhum match: marcar como `create` (nova entidade)
- Se o input ja especificou a acao: respeitar a acao do input

### 2.4 Enriquecer via fontes externas (best-effort)

Para entidades do tipo `actor` que tem campo `repository` no frontmatter:

**GitHub MCP** (chamar diretamente, NAO via subagent):
- `mcp__plugin_github_github__list_pull_requests` → PRs recentes (5, state=all, sort=updated)
- `mcp__plugin_github_github__list_commits` → commits recentes (5)

**Atlassian MCP**:
- Buscar issues do Jira do squad relevante
- Buscar paginas do Confluence relacionadas

> **IMPORTANTE:** Enrichment e best-effort. Se MCP nao estiver disponivel ou falhar, continue sem ele. Registre quais fontes falharam no relatorio final.

> **IMPORTANTE:** NAO use subagents para chamadas MCP. Permissoes nao sao herdadas por subagents.

---

## Fase 3 — Proposta de Mudancas

**Objetivo:** Apresentar ao usuario TUDO que sera feito, ANTES de executar.

### 3.1 Montar proposta

Para cada entidade, apresentar:

```
## Proposta de Mudancas — /bedrock:preserve

### Entidades a criar
| # | Tipo | Nome | Arquivo | Relacoes |
|---|---|---|---|---|
| 1 | actor | billing-new-api | actors/billing-new-api.md | [[squad-payments]], [[alice-smith]] |

### Entidades a atualizar
| # | Tipo | Nome | Arquivo | Mudancas |
|---|---|---|---|---|
| 1 | actor | billing-api | actors/billing-api.md | Adicionar secao "Atividade Recente" |

### Vinculacoes bidirecionais
| Entidade origem | Entidade destino | Secao adicionada |
|---|---|---|
| [[billing-new-api]] | [[squad-payments]] | "Related Actors" em squad-payments |
| [[squad-payments]] | [[billing-new-api]] | "team" em billing-new-api |

### Fontes consultadas
- ✅ Vault local
- ✅ / ❌ GitHub MCP
- ✅ / ❌ Atlassian MCP

Total: N entidades a criar, M a atualizar, P vinculacoes bidirecionais.
```

### 3.2 Aguardar confirmacao

Pergunte: "Confirma a execucao? (sim/nao/ajustar)"

- **sim**: prosseguir para Fase 4
- **nao**: abortar e informar
- **ajustar**: perguntar o que ajustar, modificar proposta, reapresentar

**NAO prossiga sem confirmacao explicita do usuario.**

---

## Fase 4 — Executar Mudancas

**Objetivo:** Criar e atualizar entidades conforme proposta aprovada.

### 4.1 Criar novas entidades

Para cada entidade marcada como `create`:

1. Ler o template do plugin: `<base_dir>/../../templates/<diretorio>/_template.md`
2. Preencher frontmatter com dados do input + matching:
   - `type`: tipo da entidade
   - `name` (ou `title` para topics): nome extraido
   - `aliases`: gerar pelo menos 1 alias seguindo convencao por tipo (ver conventions.md)
   - `tags`: usar tags hierarquicas: `[type/<tipo>, status/<status>, domain/<domain>]`
   - `updated_at`: data de hoje (YYYY-MM-DD)
   - `updated_by`: "preserve@agent"
   - Campos de relacao: wikilinks para entidades correlacionadas
   - Demais campos: preencher com dados do input ou deixar vazio
3. Preencher corpo seguindo estrutura do template
4. Adicionar callouts obrigatorios quando aplicavel:
   - Actors com `status: deprecated` → `> [!warning] Deprecated`
   - Actors com `pci: true` → `> [!danger] PCI Scope`
5. Salvar em `<diretorio>/<filename>.md`

**Regras por tipo de entidade:**

| Tipo | Diretorio | Filename pattern | Frontmatter key de nome |
|---|---|---|---|
| actor | actors/ ou actors/\<name\>/ | `repo-name.md` | `name` |
| knowledge-node | actors/\<actor\>/nodes/ | `node-slug.md` | `name` |
| person | people/ | `first-last.md` | `name` |
| team | teams/ | `squad-name.md` | `name` |
| topic | topics/ | `YYYY-MM-category-slug.md` | `title` |
| discussion | discussions/ | `YYYY-MM-DD-slug.md` | `title` |
| project | projects/ | `project-slug.md` | `name` |
| fleeting | fleeting/ | `YYYY-MM-DD-slug.md` | `title` |

### 4.1.2 Regras especificas para knowledge-nodes

Ao criar um knowledge-node:

1. **Resolver o ator pai:** o campo `actor` no input (wikilink ou slug) indica o ator. Verificar que o ator existe em `actors/`.
2. **Garantir estrutura de pasta:** se o ator ainda e um arquivo flat (`actors/<name>.md`):
   - Criar pasta `actors/<name>/`
   - Mover `actors/<name>.md` → `actors/<name>/<name>.md` (usar `git mv`)
   - Criar subpasta `actors/<name>/nodes/`
   - Adicionar secao "Knowledge Nodes" ao corpo do ator (antes da secao "Infraestrutura" ou no final)
3. **Criar knowledge-node:** usar template `actors/_template_node.md`
   - Salvar em `actors/<actor>/nodes/<node-slug>.md`
   - Filename: kebab-case do `name` do no (ex: `ProcessTransaction` → `process-transaction.md`)
   - Preencher `graphify_node_id`, `actor`, `node_type`, `source_file`, `confidence` a partir do input
   - Herdar `domain/*` tags do ator pai
   - Gerar pelo menos 1 alias (nome legivel + camelCase se aplicavel)
4. **Backlink bidirecional:**
   - No knowledge-node: `actor: "[[actor-name]]"` no frontmatter
   - No ator: adicionar `- [[node-slug]] — descricao breve` na secao "Knowledge Nodes"

### 4.1.1 Regras de linking por papel Zettelkasten

Ao preencher o corpo da entidade, aplicar regras de linking semantico por papel:

- **Permanent notes** (actors, people, teams): wikilinks no corpo devem ter contexto textual.
  Ex: "recebe autorizacoes do [[payment-gateway]] via gRPC" — nao apenas "[[payment-gateway]]"
- **Bridge notes** (topics, discussions): wikilinks no corpo explicam *porque* permanentes se relacionam.
  Ex: "a deprecacao do [[legacy-gateway]] esta bloqueada porque clientes dependem do [[billing-api]]"
- **Index notes** (projects): wikilinks no corpo apontam para onde o conhecimento esta.
  Ex: "progresso documentado em [[2026-06-deprecation-legacy-gateway]]"
- **Fleeting notes**: wikilinks exploratorios permitidos sem contexto textual completo.

### 4.2 Atualizar entidades existentes

Para cada entidade marcada como `update`:

1. Ler o arquivo existente
2. **Frontmatter:** merge — atualizar campos com dados novos. NUNCA apagar campos existentes.
   - SEMPRE atualizar `updated_at` e `updated_by`
   - Adicionar novos wikilinks a arrays existentes (nao duplicar)
   - Adicionar aliases novos se descobertos
3. **Corpo:**
   - **Actors:** podem ser modificados/mergeados — informacao nova substitui informacao desatualizada
   - **People, Teams, Topics:** append-only — adicionar informacao, NUNCA deletar conteudo existente
   - **Discussions, Projects:** append-only no corpo geral; campos estruturados (action_items, conclusions) podem ser atualizados
   - **Secao "Atividade Recente"** (actors): SUBSTITUIR conteudo (dados temporais)
4. **Wikilinks:** adicionar novos, NUNCA remover existentes

### 4.3 Popular campo `sources` (quando aplicavel)

Se o input contem `source_url` e `source_type` (fornecidos pelo `/bedrock:teach` ou outro caller):

**Ao criar entidade:**
- Adicionar ao frontmatter:
  ```yaml
  sources:
    - url: "<source_url>"
      type: "<source_type>"
      synced_at: "<data de hoje>"
  ```

**Ao atualizar entidade:**
1. Ler o campo `sources` existente do frontmatter
2. Se a URL ja existe na lista: atualizar `synced_at` com data de hoje
3. Se a URL nao existe: append nova entry `{url, type, synced_at}`
4. Ordenar por `synced_at` descrescente (mais recente primeiro)
5. NUNCA remover entries existentes (append-only)

**Se o input NAO contem `source_url`:** nao modificar o campo `sources` — manter o valor existente (ou `[]` se entidade nova).

---

## Fase 5 — Vinculacao Bidirecional

**Objetivo:** Garantir que toda relacao seja reciproca.

### 5.1 Regras de vinculacao

Ao criar/atualizar entidade X com referencia a entidade Y:
- Verificar se Y ja referencia X
- Se NAO: adicionar referencia de Y → X

**Grafo de vinculacao bidirecional:**

```
Team ──members──→ Person ──team──→ Team
Team ──actors──→ Actor ──team──→ Team
Topic ──people──→ Person
Topic ──actors──→ Actor
Person ──focal_points──→ Actor
Project ──focal_points──→ Person ──projects──→ Project
Project ──related_actors──→ Actor
Project ──related_topics──→ Topic
Project ──related_teams──→ Team
Discussion ──related_actors──→ Actor
Discussion ──related_people──→ Person
Discussion ──related_projects──→ Project
Discussion ──related_topics──→ Topic
Knowledge-node ──actor──→ Actor ──"Knowledge Nodes" section──→ Knowledge-node
Knowledge-node ──relations──→ Knowledge-node (bidirecional via relations[])
```

### 5.2 Implementacao

Para cada par (X → Y) na proposta aprovada:

1. Ler entidade Y
2. Identificar o campo/secao correspondente na vinculacao reversa (Y → X)
3. **No frontmatter:** se o campo de array existe, adicionar wikilink `[[X]]` se ainda nao presente
4. **No corpo:** se ha secao correspondente (ex: `## Discussions`, `## Related Projects`):
   - Se secao existe: adicionar `- [[X]] — contexto breve` ao final da lista
   - Se secao NAO existe: criar a secao no local apropriado (antes de "Expected Bidirectional Links" ou antes do ultimo `---`)
5. Atualizar `updated_at` e `updated_by` de Y
6. Salvar

**Idempotencia:** se o wikilink `[[X]]` ja existe no campo/secao de Y, NAO adicionar novamente.

### 5.3 Secoes de vinculacao por tipo de entidade destino

| Entidade destino (Y) | Secao no corpo | Campo no frontmatter |
|---|---|---|
| Actor recebendo link de Discussion | `## Discussions` | — |
| Actor recebendo link de Project | `## Related Projects` | — |
| Person recebendo link de Discussion | `## Discussions` | — |
| Person recebendo link de Project | `## Projects` | `projects` (se existir) |
| Topic recebendo link de Project | `## Related Projects` | — |

Para vinculacoes via frontmatter (team↔actor, team↔person, person↔team, etc.): usar apenas o campo YAML, nao criar secao no corpo.

---

## Fase 6 — Publicar

### 6.1 Preparar commit

Determinar mensagem de commit seguindo a convencao:

**Uma unica entidade:**
```
vault(<tipo>): <verbo> <nome> [fonte: <origem>]
```

Tipos: `ator`, `pessoa`, `time`, `assunto`, `discussion`, `project`, `source`
Verbos: `cria`, `atualiza`, `vincula`
Origens: `memoria`, `github`, `jira`, `confluence`, `gdoc`, `csv`, `manual`, `session`, `preserve`

**Multiplas entidades:**
```
vault: preserves N entities [fonte: <origens>]
```

Ou, se chamado por `/bedrock:teach`:
```
vault: teaches <source-name>, creates N updates M entities [fonte: <tipo>]
```

### 6.2 Executar git workflow

```bash
# Stage entidades tocadas (inclui subpastas de actors: actors/*/nodes/)
git add actors/ people/ teams/ topics/ discussions/ projects/ fleeting/

# Verificar se ha algo para commitar
git diff --cached --quiet && echo "Nada para commitar" && exit 0

# Commit
git commit -m "<mensagem conforme convencao>"

# Push (se remote existir)
git push origin main
```

**Se push falhar (conflito):**
```bash
git pull --rebase origin main
git push origin main
```

**Se falhar 2x:** PARE e informe o usuario.
**Se nao ha remote:** commit local e avisar.

---

## Fase 7 — Relatorio

Apresente ao usuario:

```
## Preserve — Relatorio

### Entidades criadas
| Tipo | Nome | Arquivo | Fonte |
|---|---|---|---|
| actor | payment-new-api | actors/payment-new-api.md | github |

### Entidades atualizadas
| Tipo | Nome | Arquivo | Mudancas |
|---|---|---|---|
| actor | billing-api | actors/billing-api.md | Atividade Recente, wikilinks |

### Vinculacoes bidirecionais aplicadas
| Origem | Destino | Tipo |
|---|---|---|
| [[billing-new-api]] | [[squad-payments]] | frontmatter: actors[] |
| [[squad-payments]] | [[billing-new-api]] | frontmatter: team |

### Fontes consultadas
- ✅ Vault local
- ✅ / ❌ GitHub MCP
- ✅ / ❌ Atlassian MCP

### Git
- Commit: `vault: preserves 2 entities [fonte: github]`
- Push: ✅ sucesso / ❌ falhou (motivo)

### Avisos
- [wikilinks orfaos, entidades ambiguas, MCP indisponivel, etc.]
```

---

## Regras Criticas

| # | Regra |
|---|---|
| 1 | **NUNCA deletar conteudo** escrito por outro agente ou humano (exceto secao "Atividade Recente" em actors, que e temporal) |
| 2 | **NUNCA sobrescrever frontmatter** — apenas merge de campos novos. NUNCA apagar campos existentes. |
| 3 | **NUNCA commitar dados sensiveis** (credenciais, tokens, PANs, CVVs) |
| 4 | **SEMPRE atualizar** `updated_at` e `updated_by` em toda entidade tocada |
| 5 | **SEMPRE usar kebab-case** sem acentos para filenames |
| 6 | **SEMPRE seguir os templates** de `_template.md` ao criar novas paginas |
| 7 | **SEMPRE confirmar** proposta com usuario antes de executar escrita |
| 8 | **Maximo 2 tentativas de push** — apos isso, abortar e informar |
| 9 | **Best-effort para fontes externas** — nunca bloquear por MCP indisponivel |
| 10 | **Idempotencia em wikilinks** — nao adicionar link que ja existe |
| 11 | **Frontmatter keys em ingles**, values em pt-BR |
| 12 | **Wikilinks bare** — `[[name]]`, nunca `[[dir/name]]` |
| 13 | **Tags hierarquicas** — `[type/actor]`, nunca `[actor]` |
| 14 | **Aliases obrigatorios** — pelo menos 1 alias por entidade nova |
| 15 | **Callouts obrigatorios** — `[!warning] Deprecated` para deprecated, `[!danger] PCI Scope` para PCI |
