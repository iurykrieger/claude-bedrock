---
name: sync
description: >
  Re-sincroniza o vault com fontes externas. No modo default, varre o campo `sources`
  de todas as entidades, deduplica URLs, obtem conteudo atualizado de cada fonte
  (Confluence, GDocs, GitHub, Markdown), faz diff incremental e delega escrita ao
  /bedrock:preserve. Com --people, varre repositorios dos atores via GitHub API e
  identifica contribuidores ativos. Com --github, detecta atividade relevante em
  repositorios e correlaciona PRs com topics/projects via matching semantico LLM.
  Use quando: "bedrock sync", "bedrock-sync", "/bedrock:sync", "sincronizar",
  "atualizar sources", "sync people", "sync github".
user_invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, Agent, mcp__plugin_github_github__*, mcp__plugin_atlassian_atlassian__*
---

# /bedrock:sync — Sincronizacao do Vault

## Plugin Paths

Entity definitions e templates estao no diretorio do plugin, nao na raiz do vault.
Use o "Base directory for this skill" informado na invocacao para resolver os paths:

- Entity definitions: `<base_dir>/../../entities/`
- Templates: `<base_dir>/../../templates/{type}/_template.md`
- CLAUDE.md do plugin: `<base_dir>/../../CLAUDE.md` (ja injetado automaticamente no contexto)

Onde `<base_dir>` e o path informado em "Base directory for this skill".

---

## Visao Geral

Esta skill sincroniza o vault com fontes externas. Opera em tres modos:

| Modo | Flag | Descricao |
|---|---|---|
| **Sources (default)** | _(nenhuma)_ | Re-sincroniza entidades com campo `sources` populado |
| **People** | `--people` | Varre repositorios dos atores e identifica contribuidores ativos |
| **GitHub** | `--github` | Detecta atividade em repos e correlaciona PRs com topics/projects |

---

## Roteamento

Analise o argumento passado pelo usuario:

1. Se argumento contem `--people` → ir para **Modo: Sync People** (abaixo)
2. Se argumento contem `--github` → ir para **Modo: Sync GitHub** (abaixo)
3. Caso contrario → ir para **Modo: Sync Sources (default)** (abaixo)

> **Nota:** Se nenhum argumento for passado, ou o argumento nao contiver flags reconhecidas,
> executar o modo default (Sync Sources).

---
---


# Modo: Sync Sources (default)




## Visao Geral

Esta skill varre o campo `sources` de todas as entidades do vault, deduplica por URL,
obtem conteudo atualizado de cada fonte externa, compara com as entidades ja existentes
no vault (diff incremental), e delega todas as mudancas ao `/bedrock:preserve` para escrita centralizada.

O `/bedrock:sync` **NAO escreve entidades diretamente** — toda escrita de entidades passa pelo `/bedrock:preserve`.
Apos re-sync, o `/bedrock:preserve` atualiza `synced_at` no campo `sources` das entidades afetadas.

O `/bedrock:sync` **NAO ingere fontes novas** — para isso, use `/bedrock:teach`.

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

## Fase 1 — Coletar Sources Sincronizaveis

A proveniencia esta registrada no campo `sources` do frontmatter de cada entidade.
Varra todas as entidades para coletar URLs unicas.

1. Use Grep para encontrar entidades com campo `sources` nao-vazio:
   ```
   Grep pattern "^sources:" nos diretorios: actors/, people/, teams/, topics/, discussions/, projects/, fleeting/
   ```
2. Para cada arquivo encontrado, use Read para extrair o campo `sources` do frontmatter YAML.
   Cada entry tem: `{url, type, synced_at}`
3. **Construir mapa URL → entidades:**
   Deduplicar por URL. Para cada URL unica, registrar todas as entidades que a referenciam:
   ```
   {
     "https://mycompany.atlassian.net/...": {
       type: "confluence",
       synced_at: "2026-04-09",
       entities: ["actors/billing-api.md", "topics/2026-04-feature-x.md"]
     },
     "https://github.com/acme-corp/billing-api": {
       type: "github-repo",
       synced_at: "2026-04-10",
       entities: ["actors/billing-api.md"]
     }
   }
   ```
4. **Filtrar sources sincronizaveis:**
   - Manter apenas URLs com `type` in (`confluence`, `gdoc`, `github-repo`, `markdown`)
   - Ignorar URLs com `type` = `csv` ou `manual` (logar: "URL X ignorada — tipo nao sincronizavel")
5. Armazene a lista de URLs sincronizaveis com seus mapas de entidades

Reporte: "Fase 1: N entidades com sources, M URLs unicas encontradas, K sincronizaveis, J ignoradas (tipo nao sincronizavel)."

---

## Fase 2 — Re-leitura de Fontes

Para cada source sincronizavel, obter conteudo atualizado:

### 2.1 Confluence

Para sources com `source_type: confluence`:

1. Invocar skill `/confluence-to-markdown` passando a URL da source
2. O retorno e o conteudo da pagina em formato markdown

### 2.2 Google Docs

Para sources com `source_type: gdoc`:

1. Invocar skill `/gdoc-to-markdown` passando a URL da source
2. O retorno e o conteudo do documento em formato markdown

### 2.3 Repositorio GitHub

Para sources com `source_type: github-repo`:

1. Extrair `owner/repo` da URL (segmentos de path apos `github.com/`)
2. Usar GitHub MCP diretamente (NAO via subagent — permissoes MCP nao sao herdadas):
   - `mcp__plugin_github_github__get_file_contents` → ler README.md do repo
   - `mcp__plugin_github_github__list_commits` → ultimos 10 commits
   - `mcp__plugin_github_github__list_pull_requests` → ultimos 5 PRs (state=all, sort=updated)
3. Compilar tudo em um texto markdown unico

> **Best-effort:** Se alguma chamada MCP falhar, continue com o que foi obtido. NAO bloqueie o sync.

### 2.4 Markdown local

Para sources com `source_type: markdown`:

1. Extrair o path do campo `url`
2. Use Read para ler o arquivo diretamente
3. Se o arquivo nao existir: logar e pular

### 2.5 Tratamento de erros

- Se a leitura de uma source falhar (MCP indisponivel, URL quebrada, arquivo inexistente):
  - Logar o erro: "Source X falhou — motivo"
  - Continuar com as demais sources
  - NAO abortar a execucao inteira por uma source

Reporte: "Fase 2: N sources lidas com sucesso, M falharam (listar)."

---

## Fase 3 — Diff Incremental + Extracao de Entidades

### 3.1 Carregar entity definitions

Use Read para ler TODOS os arquivos de entity definitions do plugin (ver secao "Plugin Paths"):
`<base_dir>/../../entities/*.md`
Esses arquivos definem o que cada tipo de entidade e, quando criar, e como distinguir.
Internalize essas definicoes — voce vai usa-las para classificar conteudo.

### 3.2 Catalogar entidades existentes

Use Glob para listar todos os arquivos em cada diretorio de entidades (excluindo `_template.md`):
- `actors/*.md`
- `people/*.md`
- `teams/*.md`
- `topics/*.md`
- `discussions/*.md`
- `projects/*.md`
- `fleeting/*.md`

Para cada arquivo encontrado:
- Extraia o filename sem extensao (ex: `billing-api`)
- Use Read para extrair o campo `name` (ou `title`) e `aliases` do frontmatter YAML
- Armazene: `{filename, name, aliases, tipo}` para matching

### 3.3 Analisar conteudo e detectar mudancas

Para cada source lida com sucesso na Fase 2:

1. **Identificar entidades mencionadas no conteudo atualizado:**
   - Para cada entidade catalogada na Fase 3.2, verificar se o filename, name ou alias aparece no conteudo
   - Regras de match:
     - Normalize para comparacao: lowercase, sem acentos, sem hifens
     - Match parcial aceitavel para nomes compostos (ex: "billing api" match "billing-api")
     - NAO matchar substrings de 3 letras ou menos (ex: "api" NAO match "billing-api")
     - NAO matchar palavras genericas (ex: "company", "service", "system")

2. **Comparar com `entities_generated` da source:**
   - Entidade no conteudo E ja no vault → candidata a `update` (se ha info nova no conteudo)
   - Entidade no conteudo mas NAO no vault → candidata a `create`
   - Entidade no `entities_generated` mas NAO no conteudo atualizado → **manter** (nao deletar)

3. **Classificar entidades novas:**
   - Para candidatas a `create`, consultar as entity definitions:
     - Secao "Quando criar" → criterios positivos
     - Secao "Quando NAO criar" → criterios de exclusao
     - Secao "Como distinguir de outros tipos" → desambiguacao

   > **Projetos:** `project` e um tipo valido na extracao. Ao classificar entidades novas,
   > preste atencao especial a sinais de iniciativas com escopo fechado (deadline, deliverables,
   > focal points). Consulte `entities/project.md` para criterios de criacao. Um trecho que
   > menciona migracao com deadline e responsavel provavelmente e um project, nao um topic.

4. **Registrar** para cada entidade detectada:
   - Tipo (actor, person, team, topic, discussion, project)
   - Nome canonico (filename ou slug sugerido)
   - Acao: `create` ou `update`
   - Info extraida: trecho do conteudo onde aparece
   - Source de origem: slug da source

Reporte: "Fase 3: N entidades detectadas (P creates, Q updates) em M sources."

---

## Fase 4 — Confirmacao Consolidada

**OBRIGATORIO:** Antes de criar/atualizar qualquer entidade, apresente uma lista UNICA
com todas as mudancas de TODAS as sources:

```
## Sync — Proposta de mudancas

| # | Source | Tipo | Nome | Acao | Info |
|---|---|---|---|---|---|
| 1 | roadmap-26q1 | topic | 2026-04-feature-x | create | Novo topico mencionado |
| 2 | eventos-cobranca | actor | webhook-receiver | update | Descricao atualizada |
| ... | ... | ... | ... | ... | ... |

Total: N creates, M updates em P sources.
Confirma? (sim/nao/ajustar)
```

- **sim**: prosseguir para Fase 5
- **nao**: abortar com "Sync cancelado. Nenhuma entidade modificada."
- **ajustar**: perguntar o que ajustar, modificar lista, reapresentar

**Se nenhuma mudanca detectada em nenhuma source:**
- Reportar: "Nenhuma mudanca detectada em nenhuma source. Vault ja esta atualizado."
- Pular para Fase 6 (atualizar `last_synced` mesmo assim)

**NAO prossiga sem confirmacao explicita do usuario.**

---

## Fase 5 — Delegar ao /bedrock:preserve

### 5.1 Compilar lista estruturada

Monte a lista de entidades no formato aceito pelo `/bedrock:preserve`:

```yaml
entities:
  - type: topic
    name: "2026-04-feature-x"
    action: create
    content: "trecho relevante do conteudo extraido na Fase 3..."
    relations:
      actors: ["actor-slug-1"]
      people: ["person-slug-1"]
    source: "confluence"
  - type: actor
    name: "webhook-receiver"
    action: update
    content: "novo contexto extraido na Fase 3..."
    source: "github-repo"
```

**Regras de compilacao:**
- `type` e `name`: extraidos da Fase 3
- `action`: `create` ou `update` conforme identificado
- `content`: trecho do conteudo da fonte que justifica a entidade
- `relations`: inferir relacoes entre entidades da lista (se A menciona B, incluir B nas relations de A)
- `source`: usar o `source_type` da source de origem

### 5.2 Invocar /bedrock:preserve

Use a tool Skill para invocar `/bedrock:preserve` passando a lista estruturada como argumento.

O `/bedrock:preserve` cuida de:
- Matching textual com entidades existentes
- Criacao de novas entidades seguindo templates
- Atualizacao de entidades existentes (merge/append-only)
- Vinculacao bidirecional (wikilinks)
- Git commit das entidades

### 5.3 Aguardar resultado

O `/bedrock:preserve` retorna:
- Lista de entidades criadas/atualizadas
- Commit hash (se houve commit)
- Eventuais erros ou avisos

Registre o resultado para uso no relatorio final (Fase 7).

---

## Fase 6 — Atualizar `synced_at` nas Entidades

Apos re-sync de cada URL, o `/bedrock:preserve` ja atualizou as entidades com novo conteudo.
Adicionalmente, para cada URL processada com sucesso, passar `source_url` e `source_type`
ao `/bedrock:preserve` para que ele atualize `synced_at` no campo `sources` de cada entidade mapeada.

O mapa URL → entidades (construido na Fase 1) indica quais entidades precisam ter
`synced_at` atualizado para cada URL re-sincronizada.

> **Nota:** O `/bedrock:preserve` ja faz o commit das entidades. O `/bedrock:sync` NAO faz commit separado.

---

## Fase 7 — Relatorio

Apresente ao usuario:

```
## Relatorio

| Metrica | Valor |
|---|---|
| Sources encontradas | N |
| Sources sincronizadas | N |
| Sources ignoradas (tipo) | N |
| Sources com erro | N |
| Entidades criadas | N |
| Entidades atualizadas | N |

### Por source
| Source | Tipo | Entidades | Status |
|---|---|---|---|
| roadmap-26q1 | confluence | 3 creates, 2 updates | ✅ |
| acme-corp-billing-api | github-repo | 0 creates, 1 update | ✅ |
| manual-notes | manual | — | ⏭️ ignorada |
| fonte-quebrada | confluence | — | ❌ erro (motivo) |

### Git
- Commit (entidades): <hash do /bedrock:preserve ou "nenhuma entidade">
- Commit (sources): vault: syncs N sources [fonte: sync]
- Push: ✅ sucesso / ❌ falhou (motivo)

### Sugestoes
- [sources com erro que podem ser corrigidas]
- [entidades mencionadas no conteudo mas nao criadas, se houver]
```

---

## Regras Criticas

| # | Regra |
|---|---|
| 1 | **NUNCA escrever entidades diretamente** — toda escrita de entidades passa pelo `/bedrock:preserve` |
| 2 | **NUNCA criar sources** — o `/bedrock:sync` so processa URLs ja registradas no campo `sources` das entidades |
| 3 | **NUNCA deletar entidades** — entidades ausentes no conteudo atualizado sao mantidas |
| 4 | **SEMPRE confirmar** proposta consolidada com usuario antes de executar (Fase 4) |
| 5 | **Best-effort para fontes externas** — nunca bloquear por MCP indisponivel ou URL quebrada |
| 6 | **MCP no contexto principal** — NAO usar subagents para chamadas GitHub/Atlassian MCP |
| 7 | **Sources csv e manual sao ignoradas** — tipos estaticos sem URL para re-buscar |
| 8 | **Maximo 2 tentativas de push** — apos isso, abortar e informar |
| 9 | **Dados sensiveis** — NUNCA incluir credenciais, tokens, senhas, PANs, CVVs |
| 10 | **Frontmatter keys em ingles**, values em pt-BR |
| 11 | **Wikilinks bare** — `[[name]]`, nunca `[[dir/name]]` |

---
---

# Modo: Sync People (--people)




Skill que popula `people/` a partir de commits recentes dos repositórios listados em `actors/`.

**Você é um agente de execução.** Siga as fases abaixo na ordem, sem pular etapas.
Não faça git commit/push. Não atualize `topics/` nem `actors/`. Não leia CLAUDE.md dos repositórios.

---

## Fase 1 — Coleta de atores

1. Use Glob para listar todos os arquivos `actors/*.md`
2. Exclua `actors/_template.md`
3. Para cada arquivo, use Read para extrair do frontmatter YAML:
   - `repositorio` — URL do GitHub (ex: `https://github.com/acme-corp/billing-api/`)
   - `time` — wikilink do squad (ex: `[[squad-payments]]`)
   - `nome` — nome canônico do ator (ex: `billing-api`)
4. Parsear `owner/repo` da URL: extrair os dois segmentos de path após `github.com/`
5. **Pular** atores sem campo `repositorio`, com URL vazia, ou com URL que não contenha `github.com`
6. Armazene a lista de atores válidos: `{nome, owner, repo, time_wikilink, time_slug}`
   - `time_slug`: extraído do wikilink, ex: `[[squad-payments]]` → `squad-payments`

Ao final desta fase, reporte: "Fase 1: N atores encontrados, M com repositório válido, K pulados."

---

## Fase 2 — Coleta de commits

Para cada ator da lista (em paralelo quando possível):

1. Calcule a data de 30 dias atrás no formato ISO 8601 (ex: `2026-03-04T00:00:00Z`)
2. Execute via Bash:
   ```
   gh api "repos/{owner}/{repo}/commits?since={data_30_dias}&per_page=100" 2>/dev/null
   ```
3. Se o comando falhar (404, 403, erro de rede): **logar e pular** — não falhar a execução
4. Para cada commit no resultado JSON, extrair:
   - `author.login` — login do GitHub (pode ser `null` se commit via email sem conta vinculada)
   - `commit.author.name` — display name do autor
5. **Filtrar bots:** ignorar commits onde:
   - `author.login` é `null`
   - `author.login` contém `[bot]`
   - `author.login` (case-insensitive) é exatamente: `dependabot`, `renovate`, `github-actions`, `snyk-bot`, `codecov`, `sonarcloud`, `renovate-bot`, `depfu`
6. Armazene os commits válidos associados ao ator

Ao final desta fase, reporte: "Fase 2: N repositórios acessados, M com commits, K inacessíveis (listar). Total de L commits de P contribuidores únicos."

---

## Fase 3 — Agregação

1. Agrupe todos os commits por `author.login` (lowercase)
2. Para cada pessoa única, construa:
   - `github`: login em lowercase
   - `nome`: `commit.author.name` do commit mais recente (fallback: login se nome vazio)
   - `pontos_focais`: lista de nomes canônicos de atores onde a pessoa tem commits (sem duplicatas)
   - `time_counts`: contagem de commits por squad (ex: `{squad-payments: 15, squad-notifications: 3}`)
   - `time`: squad com mais commits; em caso de empate, primeiro alfabeticamente
   - `filename`: derivado de `nome` → lowercase, sem acentos (normalizar NFD e remover combining marks), espaços→hífens, caracteres especiais removidos, kebab-case
     - Ex: `Alice Smith` → `alice-smith.md`
     - Ex: `José María` → `jose-maria.md`
     - Fallback: se nome não disponível, usar login como filename

3. **Detecção de duplicatas por filename:**
   - Se dois contribuidores (logins diferentes) gerarem o mesmo filename: appendar `-2`, `-3`, etc. ao segundo
   - Se um arquivo `people/{filename}` já existir com `github` diferente: tratar como pessoa diferente, appendar sufixo

Ao final desta fase, reporte: "Fase 3: N contribuidores únicos identificados. Distribuição por squad: [lista]."

---

## Fase 4 — Escrita de pessoas

Para cada pessoa:

### Se `people/{filename}` NÃO existe — CRIAR:

Use Write para criar o arquivo com este conteúdo exato (substitua os placeholders):

```markdown
---
tipo: pessoa
nome: "{display_name}"
cargo: ""
time: "[[{time_slug}]]"
pontos_focais: [{pontos_focais_yaml}]
github: "{github_login}"
jira: ""
atualizado_em: {data_hoje_YYYY-MM-DD}
atualizado_por: "sync-people"
tags: [pessoa]
---

# {Display Name}

> Contribuidor(a) ativo(a) identificado(a) via commits nos últimos 30 dias.

## Time

Membro de [[{time_slug}]].

## Pontos Focais

{lista_pontos_focais}

## Assuntos Ativos

_Nenhum assunto vinculado ainda._
```

Onde:
- `{pontos_focais_yaml}` = array YAML de wikilinks, ex: `["[[billing-api]]", "[[notification-service]]"]`
- `{lista_pontos_focais}` = lista markdown, ex:
  ```
  - [[billing-api]] — commits recentes
  - [[notification-service]] — commits recentes
  ```
- `{data_hoje_YYYY-MM-DD}` = data de hoje no formato `YYYY-MM-DD`

### Se `people/{filename}` JÁ existe — ATUALIZAR:

1. Use Read para ler o arquivo existente
2. **Merge `pontos_focais`:** adicionar novos atores ao array YAML existente, sem remover os que já estão lá
3. **Atualizar `time`:** sobrescrever com o novo cálculo (squad com mais commits)
4. **Atualizar `atualizado_em`:** data de hoje
5. **Atualizar `atualizado_por`:** `"sync-people"`
6. Atualizar a seção "Pontos Focais" no corpo do markdown para refletir a lista mergeada
7. Use Edit para aplicar as mudanças (não reescrever o arquivo inteiro — preservar conteúdo manual)

**Identificação por login:** Antes de criar um arquivo novo, use Grep para buscar `github: "{login}"` em `people/*.md`. Se encontrar, atualize esse arquivo em vez de criar um novo (mesmo que o filename não bata).

Ao final desta fase, reporte: "Fase 4: N pessoas criadas, M atualizadas."

---

## Fase 5 — Atualização de times

Para cada squad que recebeu novas pessoas:

1. Use Read para ler `teams/{time_slug}.md`
2. Extraia o array `membros` do frontmatter YAML
3. Para cada pessoa do squad: adicione `"[[{pessoa_filename_sem_ext}]]"` ao array se não existir
4. Atualize `atualizado_em` e `atualizado_por: "sync-people"` no frontmatter
5. Use Edit para aplicar as mudanças no frontmatter

**Não altere** nenhuma outra seção do arquivo de time.

Ao final desta fase, reporte: "Fase 5: N times atualizados. [lista de squads → quantidade de membros adicionados]."

---

## Fase 6 — Relatório final

Imprima um resumo consolidado:

```
## Sync People — Relatório

| Métrica | Valor |
|---|---|
| Atores varridos | N |
| Repositórios acessados | N |
| Repositórios inacessíveis | N |
| Commits analisados | N |
| Contribuidores encontrados | N |
| Pessoas criadas | N |
| Pessoas atualizadas | N |
| Times atualizados | N |

### Pessoas por squad

| Squad | Pessoas |
|---|---|
| squad-payments | alice, bob |
| squad-notifications | carol |
| ... | ... |

### Repositórios inacessíveis

- owner/repo — erro (se houver)
```

---

## Regras gerais

- **Idioma:** pt-BR para conteúdo, termos técnicos em inglês
- **Filenames:** kebab-case, sem acentos, lowercase
- **Wikilinks:** sem path — `[[nome]]`, nunca `[[people/nome]]`
- **Frontmatter:** YAML válido, aspas duplas para strings com caracteres especiais
- **Idempotência:** identificar pessoas por `github` login, não por filename
- **Erros:** logar e continuar — nunca falhar a execução inteira por um repo ou pessoa
- **Sem git:** não faça commit, push, ou qualquer operação git
- **Sem assuntos:** não crie/atualize arquivos em `topics/`
- **Sem atores:** não modifique arquivos em `actors/`

---
---

# Modo: Sync GitHub (--github)




## Visao Geral

Este e um **agente autonomo** projetado para rodar em background sem interacao humana.
Ele percorre todos os actors com `status: active` e campo `repository` preenchido,
busca PRs recentes via GitHub MCP, filtra ruido, usa matching semantico LLM para correlacionar
PRs com topics/projects existentes no vault, e delega atualizacoes ao `/bedrock:preserve`.

**Modo de operacao: autonomo.**
- NAO pede confirmacao — processa e escreve automaticamente
- Seguranca garantida por: (1) apenas correlacoes de ALTA confianca geram atualizacoes,
  (2) topics/projects recebem notas informativas (append), nunca sobrescrita de status,
  (3) correlacoes de media confianca sao registradas no relatorio para revisao humana
- Gera relatorio em `fleeting/` ao final de cada execucao

**Para execucao recorrente:**
- Via `/loop`: `/loop 6h /bedrock:sync --github`
- Via `/schedule`: configurar cron com este skill

O `/bedrock:sync --github` **NAO escreve entidades diretamente** — toda escrita de entidades passa pelo `/bedrock:preserve`.
Excecao: campos de watermark (`last_synced_at`, `last_synced_sha`) no frontmatter dos actors sao escritos
diretamente via Edit (nao sao entidades novas, sao metadados de sync).

O `/bedrock:sync --github` **NAO cria novos topics ou projects** — apenas atualiza existentes.

**Voce e um agente de execucao autonomo.** Siga as fases abaixo na ordem, sem pular etapas.
NAO peca confirmacao ao usuario em nenhuma fase.

---

## Fase 0 — Sincronizar o Vault

Execute:
```bash
git pull --rebase origin main
```

Se o pull falhar:
- Sem remote configurado: logar "Nenhum remote configurado. Trabalhando localmente." e prosseguir.
- Conflito no pull: `git rebase --abort`, logar o erro e **ABORTAR** a execucao inteira.
  Registrar no relatorio: "Abortado — conflito git no pull inicial."
- Caso contrario: prosseguir.

---

## Fase 1 — Coletar Actors Sincronizaveis

1. Use Glob para listar todos os arquivos `actors/*.md`
2. Exclua `actors/_template.md`
3. Para cada arquivo, use Read para extrair do frontmatter YAML:
   - `status` — status do actor
   - `repository` — URL do repositorio GitHub
   - `name` — nome do actor
   - `last_synced_at` — data do ultimo sync GitHub (pode nao existir)
   - `last_synced_sha` — SHA do ultimo sync (pode nao existir)
4. **Filtrar actors sincronizaveis:**
   - Manter apenas actors com `status: active` (ou `in-development`)
   - Manter apenas actors com campo `repository` preenchido e contendo `github.com`
   - Ignorar actors com `status: deprecated` (logar: "Actor X ignorado — deprecated")
   - Ignorar actors sem `repository` ou com URL invalida (logar: "Actor X ignorado — sem repositorio GitHub")
5. Para cada actor sincronizavel, extrair `owner/repo` da URL:
   - Parsear a URL: `https://github.com/<owner>/<repo>/` → `owner`, `repo`
   - Remover trailing slashes e `.git` suffix se presente
6. Armazene a lista de actors sincronizaveis com: `{filename, name, owner, repo, last_synced_at, last_synced_sha}`

Logar: "Fase 1: N actors encontrados, M sincronizaveis, K ignorados (deprecated/sem repo)."

---

## Fase 2 — Fetch PRs via GitHub MCP

Para cada actor sincronizavel, buscar PRs recentes:

1. Usar GitHub MCP diretamente (NAO via Agent tool — permissoes MCP nao sao herdadas por subagents):
   - `mcp__plugin_github_github__list_pull_requests` com parametros:
     - `owner`: owner do repo
     - `repo`: repo name
     - `state`: "all" (open, merged, closed)
     - `sort`: "updated"
     - `per_page`: 20
2. **Filtrar por watermark:**
   - Se o actor tem `last_synced_at`: manter apenas PRs com `updated_at` >= `last_synced_at`
   - Se o actor NAO tem `last_synced_at`: manter apenas PRs dos ultimos 30 dias
3. Registrar para cada PR:
   - `number`, `title`, `body` (descricao), `state` (open/closed), `merged` (bool)
   - `user.login` (autor)
   - `updated_at`, `created_at`
   - `head.sha` (ultimo commit SHA)

> **Best-effort:** Se a chamada MCP falhar para um actor (rate limit, repo privado, URL invalida):
> - Logar o erro: "Actor X falhou — motivo"
> - Continuar com os demais actors
> - NAO abortar a execucao inteira por um actor

> **Skip rapido:** Se nenhuma PR foi retornada ou todas as PRs sao anteriores ao watermark,
> logar "Actor X — sem atividade relevante" e pular para o proximo actor.

Logar: "Fase 2: N actors consultados, M com PRs relevantes, K sem atividade, J com erro."

---

## Fase 3 — Filtrar Ruido

Para cada PR coletada na Fase 2, aplicar filtros de ruido:

### 3.1 Filtro por autor
Remover PRs de bots e ferramentas automatizadas:
- Autor contem `[bot]` ou `bot` no login (ex: `dependabot[bot]`, `renovate[bot]`, `github-actions[bot]`)
- Autor e `dependabot`, `renovate`, `snyk-bot`, `greenkeeper`

### 3.2 Filtro por titulo
Remover PRs com titulos indicando mudancas automaticas ou irrelevantes:
- Titulo comeca com: `Bump `, `chore(deps)`, `build(deps)`, `Update dependency`
- Titulo contem: `version bump`, `dependency update`, `auto-merge`
- Titulo e apenas um numero de versao (ex: `v1.2.3`, `1.2.3`)

### 3.3 Registrar resultado
Para cada actor, manter lista de PRs relevantes (pos-filtro).
Se todas as PRs de um actor foram filtradas: logar "Actor X — todas PRs filtradas (ruido)" e pular.

Logar: "Fase 3: N PRs totais, M relevantes apos filtro, K filtradas como ruido."

---

## Fase 4 — Matching Semantico LLM

### 4.1 Carregar catalogo de topics e projects

Use Glob + Read para coletar:

**Topics (`topics/*.md`, excluindo `_template.md`):**
- `filename` (sem extensao)
- `title`
- `aliases`
- `status` (open, in-progress, completed, cancelled)
- `actors` (lista de wikilinks)
- `objective`
- `category`

**Projects (`projects/*.md`, excluindo `_template.md`):**
- `filename` (sem extensao)
- `name`
- `aliases`
- `status` (planning, active, blocked, completed)
- `related_actors` (lista de wikilinks)
- `blockers`
- `action_items` (lista com description, status)
- `progress`

Armazene como catalogo para matching.

### 4.2 Preparar batch de matching

Para cada actor com PRs relevantes, monte um bloco:

```
Actor: <actor-name> (<owner>/<repo>)
PRs relevantes:
- PR #<number>: "<title>" (state: <open|closed|merged>, autor: <login>, data: <date>)
  Descricao: <primeiros 200 chars do body>
- PR #<number>: ...
```

### 4.3 Executar matching semantico

Com o catalogo de topics/projects e o batch de PRs, analise semanticamente:

Para cada PR relevante, determine:

1. **Correlacao com topic/project:** A PR se relaciona com algum topic ou project existente?
   - Considere: titulo da PR, descricao, actor de origem, aliases dos topics/projects
   - Match por: tema (deprecacao, feature, bugfix), sistema mencionado, objetivo alinhado
   - NAO matchar genericamente — exija relacao semantica clara

2. **Implicacao de status:** Se ha correlacao, a PR implica mudanca de status?
   - PR mergeada em actor listado num topic "open" → sugere status "in-progress" ou "completed"
   - PR mergeada que resolve um blocker de project → sugere remocao do blocker
   - PR aberta para feature de topic "blocked" → sugere status "in-progress"
   - PR fechada sem merge → sem implicacao de status

3. **Classificacao da mudanca:**
   - `status_hint` — status sugerido (ex: "in-progress", "completed")
   - `evidence` — descricao da evidencia (ex: "PR #42 mergeada implementa feature X do topic Y")
   - `confidence` — alta, media, baixa
   - `entity_type` — "topic" ou "project"
   - `entity_name` — filename do topic/project

**Regras de matching:**
- Priorize matches de alta confianca (titulo da PR menciona explicitamente o topic/projeto)
- Descarte matches de baixa confianca (correlacao vaga, apenas por dominio)
- Se nenhuma PR de um actor tem correlacao: registrar "sem correlacao" e prosseguir
- NAO criar novos topics/projects — apenas correlacionar com existentes

### 4.4 Classificar resultados por nivel de acao

Separar correlacoes em dois grupos:

**ALTA confianca → acao automatica:**
- Serao processadas automaticamente na Fase 5 (sem confirmacao humana)
- Criterio: titulo da PR menciona explicitamente o topic/projeto, OU a PR esta em actor
  listado no frontmatter `actors`/`related_actors` do topic/project E o tema da PR
  alinha com o `objective` do topic ou `progress`/`action_items` do project

**MEDIA confianca → apenas relatorio:**
- NAO serao processadas automaticamente
- Serao registradas no relatorio final (Fase 7) para revisao humana
- Criterio: correlacao semantica plausivel mas sem evidencia explicita

Logar: "Fase 4: N correlacoes (P alta confianca → acao, Q media confianca → relatorio). R actors com atividade sem correlacao."

---

## Fase 5 — Delegar ao /bedrock:preserve e Atualizar Actors

### 5.1 Compilar lista para /bedrock:preserve

Monte a lista de entidades no formato aceito pelo `/bedrock:preserve`.
**Incluir APENAS correlacoes de ALTA confianca + atividade de actors.**

**Para topics com correlacao ALTA:**
```yaml
- type: topic
  name: "filename-do-topic"
  action: update
  content: |
    ## Atividade GitHub (sync-github YYYY-MM-DD)

    | PR | Repo | Status | Evidencia |
    |---|---|---|---|
    | #42 | billing-api | merged | Implementa feature X |

    > [!info] Status sugerido: in-progress
    > Baseado em PR #42 mergeada em billing-api que implementa feature X.
    > Detectado automaticamente por sync-github@agent.
  source: "github"
```

**Para projects com correlacao ALTA:**
```yaml
- type: project
  name: "filename-do-project"
  action: update
  content: |
    ## Atividade GitHub (sync-github YYYY-MM-DD)

    | PR | Repo | Status | Evidencia |
    |---|---|---|---|
    | #15 | orders-api | merged | Resolve blocker Y |

    > [!info] Status sugerido: active
    > Baseado em PR #15 mergeada em orders-api que resolve blocker Y.
    > O status do projeto reflete uma decisao de gestao — revise esta sugestao.
    > Detectado automaticamente por sync-github@agent.
  source: "github"
```

**Para actors com atividade relevante (todos, nao apenas com correlacao):**
```yaml
- type: actor
  name: "actor-name"
  action: update
  content: |
    ## Atividade Recente (sync-github YYYY-MM-DD)

    | PR | Titulo | Status | Autor | Data |
    |---|---|---|---|---|
    | #42 | Feature X | merged | alice | 2026-04-10 |
    | #34 | Refatoracao Y | open | bob | 2026-04-09 |
  source: "github"
```

**Regras de compilacao:**
- Conteudo para topics/projects: append-only. Adicionar secao "Atividade GitHub" com callout `[!info]` sugerindo status. NUNCA sobrescrever o campo `status` diretamente.
- Conteudo para actors: merge-ok. A secao "Atividade Recente" substitui a versao anterior (se existir).
- `source: "github"` para todas as entidades
- Wikilinks bare: `[[actor-name]]`, nunca `[[actors/actor-name]]`

### 5.2 Invocar /bedrock:preserve

Use a tool Skill para invocar `/bedrock:preserve` passando a lista estruturada como argumento.

> **IMPORTANTE para execucao em background:** Ao invocar `/bedrock:preserve`, inclua na
> instrucao que o `/bedrock:preserve` tambem deve operar sem confirmacao humana.
> Adicione ao prompt: "Modo autonomo — nao pedir confirmacao, processar diretamente."

O `/bedrock:preserve` cuida de:
- Matching textual com entidades existentes
- Atualizacao de entidades existentes (merge/append-only)
- Vinculacao bidirecional (wikilinks)
- Git commit das entidades

### 5.3 Atualizar watermarks dos actors

Apos o `/bedrock:preserve` completar, atualize o frontmatter de CADA actor processado (com ou sem correlacao):

1. Use Read para ler o arquivo do actor
2. Use Edit para atualizar no frontmatter:
   - `last_synced_at`: data de hoje (YYYY-MM-DD)
   - `last_synced_sha`: SHA do commit mais recente da PR mais recente (ou manter anterior se nenhuma PR)
   - `updated_at`: data de hoje
   - `updated_by`: `"sync-github@agent"`
3. Se os campos `last_synced_at` e `last_synced_sha` nao existem: adiciona-los ao frontmatter (antes de `updated_at`)

### 5.4 Git commit dos watermarks

```bash
git add actors/
git diff --cached --quiet && echo "Nada para commitar" && exit 0
git commit -m "vault(source): syncs github activity for N actors [fonte: github]"
git push origin main
```

**Se push falhar (conflito):**
```bash
git pull --rebase origin main
git push origin main
```

**Se falhar 2x:** Logar o erro e continuar para o relatorio.
**Se nao ha remote:** Commit local e logar.

---

## Fase 6 — Gerar Relatorio

Gerar um relatorio completo da execucao e salvar como fleeting note.

### 6.1 Montar conteudo do relatorio

```markdown
---
type: fleeting
name: "sync-github YYYY-MM-DD"
aliases: ["Sync GitHub YYYY-MM-DD"]
status: "raw"
updated_at: YYYY-MM-DD
updated_by: "sync-github@agent"
tags: [type/fleeting, status/raw]
---

# Sync GitHub — YYYY-MM-DD

> Relatorio automatico gerado por sync-github@agent.

## Resumo

| Metrica | Valor |
|---|---|
| Actors encontrados | N |
| Actors sincronizados | N |
| Actors ignorados (deprecated/sem repo) | N |
| Actors com erro (MCP) | N |
| PRs coletadas | N |
| PRs relevantes (pos-filtro) | N |
| PRs filtradas (ruido) | N |
| Correlacoes alta confianca (processadas) | N |
| Correlacoes media confianca (para revisao) | N |
| Actors com atividade (sem correlacao) | N |

## Correlacoes Processadas (Alta Confianca)

| Actor | PR | Entidade | Tipo | Status Sugerido | Evidencia |
|---|---|---|---|---|---|
| [[billing-api]] | #42 | [[2026-04-feature-x]] | topic | in-progress | PR implementa feature X |
| ... | ... | ... | ... | ... | ... |

## Correlacoes para Revisao Humana (Media Confianca)

> [!todo] Revisar correlacoes abaixo
> Estas correlacoes foram detectadas com confianca media. Revise e aplique manualmente se corretas.

| Actor | PR | Entidade | Tipo | Status Sugerido | Evidencia |
|---|---|---|---|---|---|
| [[notification-service]] | #33 | [[2026-04-bugfix-timeout-notifications]] | topic | in-progress | PR titulo menciona timeout |
| ... | ... | ... | ... | ... | ... |

## Atividade por Actor

| Actor | PRs Relevantes | Resumo |
|---|---|---|
| [[billing-api]] | #42 merged, #43 open | Feature X concluida, refatoracao Y em progresso |
| [[notification-service]] | #33 merged | Fix de timeout |
| ... | ... | ... |

## Actors Atualizados (Watermark)

| Actor | last_synced_at | last_synced_sha |
|---|---|---|
| [[billing-api]] | YYYY-MM-DD | abc1234 |
| ... | ... | ... |

## Erros

| Actor | Erro |
|---|---|
| actor-x | MCP timeout |
| ... | ... |

## Git

- Commit (entidades): <hash do /bedrock:preserve ou "nenhuma entidade">
- Commit (watermarks): vault(source): syncs github activity [fonte: github]
- Push: sucesso / falhou (motivo)
```

### 6.2 Salvar relatorio

Salvar o relatorio em `fleeting/YYYY-MM-DD-sync-github.md`.

Se o arquivo ja existir (execucao duplicada no mesmo dia): sobrescrever com dados mais recentes.

### 6.3 Git commit do relatorio

```bash
git add fleeting/
git diff --cached --quiet && echo "Nada para commitar" && exit 0
git commit -m "vault(nota): cria relatorio sync-github YYYY-MM-DD [fonte: github]"
git push origin main
```

**Se push falhar:** rebase + retry (max 2x).

---

## Fase 7 — Finalizar

Logar mensagem final:

```
sync-github@agent finalizado.
- Actors processados: N
- Correlacoes processadas (alta): N
- Correlacoes para revisao (media): N
- Relatorio: fleeting/YYYY-MM-DD-sync-github.md
```

**A execucao termina aqui.** O agente nao espera resposta do usuario.

---

## Regras Criticas

| # | Regra |
|---|---|
| 1 | **MODO AUTONOMO** — NAO pedir confirmacao ao usuario em nenhuma fase |
| 2 | **NUNCA escrever entidades diretamente** — toda escrita de topics/projects/actors passa pelo `/bedrock:preserve` |
| 3 | **NUNCA criar novos topics ou projects** — apenas atualizar existentes |
| 4 | **NUNCA sobrescrever status** de topics/projects — apenas adicionar nota com sugestao via callout `[!info]` |
| 5 | **Apenas ALTA confianca gera acao** — correlacoes de media confianca vao apenas para o relatorio |
| 6 | **Best-effort para GitHub MCP** — nunca bloquear por rate limit ou repo inacessivel |
| 7 | **MCP no contexto principal** — NAO usar Agent tool para chamadas GitHub MCP |
| 8 | **Filtrar ruido antes do matching** — dependabot, version bumps, bots |
| 9 | **Matching semantico conservador** — descartar correlacoes de baixa confianca |
| 10 | **Maximo 2 tentativas de push** — apos isso, logar e continuar |
| 11 | **Dados sensiveis** — NUNCA incluir credenciais, tokens, senhas, PANs, CVVs |
| 12 | **Frontmatter keys em ingles**, values em pt-BR |
| 13 | **Wikilinks bare** — `[[name]]`, nunca `[[dir/name]]` |
| 14 | **Append-only para topics** — adicionar informacao, nunca deletar conteudo existente |
| 15 | **Relatorio sempre gerado** — mesmo se nenhuma correlacao, gerar relatorio em `fleeting/` |
