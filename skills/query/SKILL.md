---
name: query
description: >
  Skill de leitura inteligente do vault. Recebe uma pergunta em linguagem natural,
  varre o vault em busca da informacao, cruza contexto entre entidades via wikilinks,
  prioriza informacao recente, e opcionalmente busca fontes externas delegando para
  skills conhecidas (/confluence-to-markdown, /gdoc-to-markdown, GitHub MCP).
  Use quando: "bedrock query", "bedrock-query", "/bedrock:query", qualquer pergunta sobre o vault, "o que sabemos sobre",
  "quem cuida de", "qual o status de", "me fala sobre", "como funciona", ou qualquer
  consulta ao Second Brain.
user_invocable: true
allowed-tools: Bash, Read, Glob, Grep, Skill, Agent, mcp__plugin_github_github__get_file_contents, mcp__plugin_github_github__list_commits, mcp__plugin_github_github__list_pull_requests
---

# /bedrock:query — Leitura Inteligente do Vault

## Plugin Paths

Entity definitions e templates estao no diretorio do plugin, nao na raiz do vault.
Use o "Base directory for this skill" informado na invocacao para resolver os paths:

- Entity definitions: `<base_dir>/../../entities/`
- Templates: `<base_dir>/../../templates/{type}/_template.md`
- CLAUDE.md do plugin: `<base_dir>/../../CLAUDE.md` (ja injetado automaticamente no contexto)

Onde `<base_dir>` e o path informado em "Base directory for this skill".

---

## Visao Geral

Esta skill recebe uma pergunta em linguagem natural, varre o vault para encontrar a resposta,
cruza contexto entre entidades via wikilinks, prioriza informacao recente, e opcionalmente
busca fontes externas quando a informacao local e insuficiente.

**Voce e um agente de consulta. Voce so LE — nunca escreve, edita, ou deleta arquivos.**

Se a consulta revelar informacao desatualizada ou ausente, sugira ao usuario rodar
`/bedrock:preserve` ou `/bedrock:teach` para atualizar o vault. Nunca faca a atualizacao voce mesmo.

---

## Fase 1 — Analisar a Pergunta

### 1.1 Classificar a pergunta

Leia a pergunta do usuario e identifique:

1. **Entidades mencionadas** — nomes de sistemas, pessoas, times, assuntos, projetos, ou discussoes.
   Podem aparecer como:
   - Nome exato do arquivo (ex: "billing-api", "squad-payments")
   - Nome legivel (ex: "Billing API", "Squad Payments")
   - Alias ou sigla (ex: "BillingAPI", "BRB")
   - Referencia contextual (ex: "o servico de cobranca", "o time de notificacoes")

2. **Dominio(s) relevante(s)** — `payments`, `notifications`, `orders`, `integrations`, `checkout`, `compliance`, `internal-tools`.
   Inferir a partir das entidades mencionadas ou do contexto da pergunta.

3. **Tipo de informacao buscada:**
   - **Status/overview** — "o que e X?", "qual o status de X?"
   - **Arquitetura/stack** — "como funciona X?", "qual a stack de X?"
   - **Pessoas/times** — "quem cuida de X?", "quem trabalha com Y?"
   - **Historico/decisoes** — "o que foi decidido sobre X?", "o que aconteceu com Y?"
   - **Relacoes** — "o que depende de X?", "o que Y tem a ver com Z?"
   - **Deprecacao** — "o que esta sendo descontinuado?", "qual o plano de deprecacao de X?"

### 1.2 Avaliar clareza

Se a pergunta e ambigua demais para produzir uma busca direcionada (ex: "me conta tudo",
"como funciona o sistema?", "o que esta acontecendo?"), peca clarificacao:

> "Sua pergunta e ampla. Pode especificar: qual sistema, time, ou assunto voce quer saber mais?"

Se a pergunta menciona algo que claramente nao faz parte do vault (ex: algo pessoal,
tecnologia nao relacionada), informe: "Nao encontrei nada no vault sobre isso."

### 1.3 Resultado da Fase 1

Ao final, voce deve ter:
- **termos_de_busca**: lista de nomes, aliases, e palavras-chave para buscar
- **dominios**: lista de dominios relevantes (pode ser vazia se nao identificado)
- **tipo_de_info**: classificacao do tipo de informacao buscada
- **entidades_explicitas**: entidades mencionadas diretamente pelo nome (se houver)

---

## Fase 1.5 — Verificar Grafo de Conhecimento (graphify)

Antes da busca no vault, verificar se o grafo de conhecimento do graphify esta disponivel.
O grafo habilita traversal semantico (BFS/DFS) que complementa e prioriza sobre a busca
sequencial por Glob/Grep.

### 1.5.1 Verificar graph.json

```bash
# Verificar se graphify-out/graph.json existe e nao esta vazio
if [ -f "graphify-out/graph.json" ] && [ -s "graphify-out/graph.json" ]; then
    $(cat graphify-out/.graphify_python 2>/dev/null || echo python3) -c "
import json
from pathlib import Path
g = json.loads(Path('graphify-out/graph.json').read_text())
nodes = len(g.get('nodes', []))
edges = len(g.get('edges', []))
communities = len(g.get('communities', {}))
print(f'Graph disponivel: {nodes} nos, {edges} edges, {communities} communities')
"
else
    echo "Graph nao disponivel"
fi
```

- **Se graph.json existe e nao esta vazio:** setar `graph_available = true`. Reportar: "Grafo de conhecimento disponivel (N nos, M edges, K communities)."
- **Se graph.json NAO existe ou esta vazio:** setar `graph_available = false`. Prosseguir para Fase 2 usando busca sequencial (Glob/Grep) sem alteracao.

### 1.5.2 Verificar labels de communities (opcional)

Se `graph_available = true`, verificar se `graphify-out/.graphify_labels.json` existe.
Se sim: carregar labels para uso na Fase 2.5 (explorar communities por dominio).

---

## Fase 2 — Busca Local no Vault

**Se `graph_available = true`:** usar Fase 2-G (graphify-first) abaixo.
**Se `graph_available = false`:** usar Fase 2-S (sequencial) — o fluxo existente sem alteracao.

### Fase 2-G — Busca via Graphify (quando graph_available = true)

O graphify query faz traversal no grafo de conhecimento e retorna nos e edges relevantes.
Isso substitui os Passos 1-4 da busca sequencial para a maioria das perguntas, mas a busca
sequencial continua disponivel como complemento para entidades fora do grafo (people, teams).

#### 2-G.1 Formular a query

A partir dos resultados da Fase 1 (termos_de_busca, tipo_de_info, entidades_explicitas):

- **Perguntas de relacao** ("o que depende de X?", "quais servicos usam Y?", "como X se conecta com Y?"):
  Usar a pergunta original do usuario como query.
- **Perguntas de status/overview** ("o que e X?", "qual a stack de X?"):
  Reformular para focar na entidade: `"<entity-name>"`
- **Perguntas amplas** ("me fala sobre o dominio payments"):
  Pular para Fase 2.5 (explorar communities).

#### 2-G.2 Executar graphify query

Escolher o modo de traversal:
- **BFS (default)** — para contexto amplo (vizinhanca de um no). Usar para a maioria das perguntas.
- **DFS** — para path-finding ("como X se conecta com Y", "qual o caminho de X a Y").

```bash
$(cat graphify-out/.graphify_python) -c "
from graphify.query import query
result = query('<pergunta-do-usuario>', budget=1500)
# result contem: nodes relevantes, edges, score de relevancia
import json; print(json.dumps(result, indent=2))
"
```

**Budget de tokens:** default 1500 (suficiente para 10-15 nos com descricoes). Se o usuario
pedir explicitamente mais contexto: aumentar para 3000.

Para path-finding entre dois conceitos:
```bash
$(cat graphify-out/.graphify_python) -c "
from graphify.query import find_path
result = find_path('<nodeA>', '<nodeB>')
import json; print(json.dumps(result, indent=2))
"
```

Para explicacao de um no especifico:
```bash
$(cat graphify-out/.graphify_python) -c "
from graphify.query import explain
result = explain('<node-name>')
import json; print(json.dumps(result, indent=2))
"
```

#### 2-G.3 Resolver nos para arquivos .md do vault

Para cada no retornado pelo graphify query:

1. Extrair `id` (graphify_node_id) e `label` do no
2. Resolver para arquivo .md no vault:
   - **Nos com `source_file` apontando para actors:** buscar knowledge-node em `actors/*/nodes/` via `graphify_node_id` no frontmatter, ou buscar o ator pai em `actors/`
   - **Nos com label que matcha um filename de entidade:** Glob para `actors/<label>*.md`, `topics/*<label>*.md`, etc.
   - **Se nao resolver:** registrar como "no sem .md correspondente" — sera mencionado na resposta
3. Ler os .md resolvidos (frontmatter + corpo) — limite: 15 entidades total

#### 2-G.4 Complementar com busca sequencial

O graphify nao indexa people e teams diretamente (sao entidades do vault, nao do codigo).
Para perguntas que envolvem people/teams:

1. Usar Glob/Grep para buscar em `people/` e `teams/` pelos termos de busca da Fase 1
2. Adicionar resultados aos ja obtidos do graphify
3. Respeitar limite total de 15 entidades

### Fase 2-S — Busca Sequencial (quando graph_available = false)

Quando o grafo nao esta disponivel, usar o fluxo original sem alteracao:

### 2.1 Ler entity definitions

Use Read para ler os arquivos de entity definitions do plugin (ver secao "Plugin Paths"):
- Se a pergunta e sobre um sistema → ler `<base_dir>/../../entities/actor.md`
- Se a pergunta e sobre uma pessoa → ler `<base_dir>/../../entities/person.md`
- Se a pergunta e sobre um time → ler `<base_dir>/../../entities/team.md`
- Se a pergunta e sobre um assunto/deprecacao → ler `<base_dir>/../../entities/topic.md`
- Se a pergunta e sobre uma reuniao/decisao → ler `<base_dir>/../../entities/discussion.md`
- Se a pergunta e sobre um projeto/iniciativa → ler `<base_dir>/../../entities/project.md`
- Se nao sabe o tipo → ler todos os entity definitions do plugin para classificar corretamente

### 2.2 Buscar entidades por nome e alias

Para cada termo de busca identificado na Fase 1:

**Passo 1 — Busca por filename:**
```
Glob: actors/<termo>*.md, people/<termo>*.md, teams/<termo>*.md,
      topics/*<termo>*.md, discussions/*<termo>*.md, projects/<termo>*.md,
      sources/<termo>*.md, fleeting/*<termo>*.md
```

**Passo 2 — Busca por alias no frontmatter:**
```
Grep: pattern="aliases:.*<termo>" nos diretorios: actors/, people/, teams/,
      topics/, discussions/, projects/
      (case-insensitive)
```

**Passo 3 — Busca por nome no frontmatter:**
```
Grep: pattern="name:.*<termo>" ou pattern="title:.*<termo>"
      nos mesmos diretorios (case-insensitive)
```

**Passo 4 — Busca por conteudo (fallback):**
Se os passos 1-3 nao retornaram resultados suficientes:
```
Grep: pattern="<termo>" nos diretorios de entidades (case-insensitive)
```

### 2.3 Filtrar por dominio

Se dominios foram identificados na Fase 1, filtrar resultados:
```
Grep: pattern="domain/<dominio>" nos arquivos encontrados (campo tags do frontmatter)
```

Manter todos os resultados, mas priorizar os que matcham o dominio.

### 2.4 Ler entidades encontradas

Para cada entidade encontrada (limite: 15 entidades):

1. Ler o frontmatter primeiro (primeiras ~30 linhas) para confirmar relevancia
2. Se relevante: ler o arquivo completo
3. Se nao relevante (false positive no Grep): descartar

Registrar para cada entidade lida:
- filename, tipo, nome
- wikilinks encontradas no frontmatter e corpo
- URLs externas encontradas no conteudo (Confluence, Google Docs, GitHub)
- Data explicita no filename (se houver)

---

## Fase 2.5 — Explorar Communities (quando graph_available = true e pergunta ampla)

Quando a pergunta e ampla e nao menciona entidades especificas (ex: "me fala sobre o dominio payments",
"o que esta acontecendo com notifications?", "visao geral do processing"):

### 2.5.1 Identificar community relevante

1. Ler `graphify-out/.graphify_labels.json` (se existir) — contem labels legives por community
2. Procurar community cujo label matcha o dominio ou tema da pergunta
3. Se nenhum label matcha: pular esta fase e usar Fase 2-G com a pergunta original

### 2.5.2 Listar nos da community

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
graph = json.loads(Path('graphify-out/graph.json').read_text())
# Filtrar nos pela community identificada
community_nodes = [n for n in graph.get('nodes', []) if n.get('community') == <community_id>]
print(json.dumps(community_nodes[:20], indent=2))  # top 20 nos da community
"
```

### 2.5.3 Resolver e ler .md

Para cada no da community (limite: 10 nos):
1. Resolver para arquivo .md no vault (mesma logica de 2-G.3)
2. Ler frontmatter para overview rapido
3. Priorizar nos com maior grau (mais edges) — sao os "god nodes" da community

Resultado: visao geral do dominio baseada na estrutura do grafo, nao em busca textual.

---

## Fase 3 — Cruzar Contexto via Wikilinks

> **Nota:** Quando `graph_available = true`, o graphify ja retorna nos conectados via edges.
> O cruzamento via wikilinks nesta fase e **complementar** — usado principalmente para entidades
> que nao estao no grafo (people, teams, sources, fleeting). Se os resultados da Fase 2-G ja
> cobrem a pergunta com 15 entidades, esta fase pode ser reduzida ou pulada.

### 3.1 Extrair wikilinks das entidades encontradas

Para cada entidade lida na Fase 2, extrair todas as wikilinks (`[[...]]`) do:
- Frontmatter: campos como `team`, `members`, `actors`, `people`, `focal_points`,
  `related_topics`, `related_actors`, `related_teams`, `related_people`, `related_projects`
- Corpo: wikilinks inline no texto

### 3.2 Seguir wikilinks (1 nivel de profundidade)

Para cada wikilink extraida que seja relevante para a pergunta:

1. Resolver o arquivo: procurar `<wikilink-name>.md` nos diretorios de entidades
   ```
   Glob: actors/<name>.md, people/<name>.md, teams/<name>.md,
         topics/*<name>*.md, discussions/*<name>*.md, projects/<name>.md
   ```

2. Ler o arquivo encontrado (frontmatter + corpo)

3. **NAO seguir wikilinks deste segundo nivel** — parar aqui para evitar explosao de contexto

**Criterios de relevancia para seguir um wikilink:**
- A pergunta e sobre relacoes ("quem cuida de", "o que depende de") → seguir todos
- A pergunta e sobre status/overview → seguir team, people (focal points)
- A pergunta e sobre historico → seguir discussions, topics relacionados
- A pergunta e sobre arquitetura → seguir actors dependentes

**Limite:** Nao ler mais de 15 entidades no total (Fase 2 + Fase 3 combinados).
Se o limite for atingido, priorizar entidades diretamente mencionadas na pergunta.

---

## Fase 4 — Priorizar por Recencia

### 4.1 Identificar entidades com data explicita

Para discussions e topics, extrair a data do filename:
- Padrao `YYYY-MM-DD-slug.md` → data completa (ex: `2026-04-02`)
- Padrao `YYYY-MM-slug.md` → data parcial, assumir dia 01 (ex: `2026-04-01`)

Para entidades consolidadas (actors, people, teams, projects, sources):
- Tratar como igualmente atualizadas — nao aplicar ranking temporal
- Confiar que o conteudo esta atualizado via `/bedrock:preserve` e `/bedrock:compress`

### 4.2 Ordenar por recencia

Quando a resposta envolver multiplas discussions ou topics datados:
- Ordenar por data decrescente (mais recente primeiro)
- Se a pergunta e explicitamente sobre algo recente ("o que aconteceu ultimamente",
  "ultimas decisoes"), limitar a entidades dos ultimos 30 dias
- Se a pergunta e sobre historico ("o que aconteceu com X ao longo do tempo"),
  incluir todas as datas mas apresentar cronologicamente (mais recente primeiro)

---

## Fase 5 — Fetch Externo (Quando Necessario)

### 5.1 Avaliar necessidade

Fetch externo so e necessario quando:
1. A informacao local e insuficiente para responder a pergunta, E
2. As entidades consultadas contem URLs externas relevantes

Se a informacao local e suficiente: **pular esta fase inteira**.

### 5.2 Identificar URLs externas

Nas entidades lidas (Fase 2 e 3), procurar URLs:
- Confluence: URLs contendo `confluence` ou `atlassian.net`
- Google Docs: URLs contendo `docs.google.com`
- GitHub: URLs contendo `github.com` (repositorios, issues, PRs)

### 5.3 Delegar leitura para skill correspondente

Para cada URL relevante (limite: 3 URLs externas por consulta):

| URL contém | Acao |
|---|---|
| `confluence` ou `atlassian.net` | Invocar skill `/confluence-to-markdown` passando a URL |
| `docs.google.com` | Invocar skill `/gdoc-to-markdown` passando a URL |
| `github.com` com path de arquivo | Usar `mcp__plugin_github_github__get_file_contents` com owner, repo, e path extraidos da URL |
| `github.com` sem path (repo root) | Usar `mcp__plugin_github_github__get_file_contents` para ler README.md + `mcp__plugin_github_github__list_commits` para ultimos 5 commits |

**Regras de fetch externo:**
- **Best-effort:** Se a skill ou MCP falhar, continue com a informacao local. Nunca bloqueie a resposta.
- **1 nivel apenas:** Nao seguir links encontrados dentro do documento externo.
- **Limite de 3 URLs:** Se houver mais de 3 URLs relevantes, priorizar as que parecem mais diretamente relacionadas a pergunta.

### 5.4 Integrar conteudo externo

Incorporar o conteudo obtido ao contexto da resposta. Marcar claramente a origem:
- "(fonte: Confluence — <titulo da pagina>)"
- "(fonte: Google Docs — <titulo do doc>)"
- "(fonte: GitHub — <owner/repo>)"

---

## Fase 6 — Responder ao Usuario

### 6.1 Montar a resposta

Construa a resposta seguindo estas regras:

1. **Idioma:** pt-BR. Termos tecnicos em ingles sao aceitos (PCI DSS, API, EKS, etc.)

2. **Estrutura da resposta:**
   - Abrir com resposta direta a pergunta (1-3 frases)
   - Se necessario, expandir com detalhes organizados por topico
   - Usar headers (`##`, `###`) se a resposta for longa (>5 paragrafos)
   - Usar tabelas quando a informacao for comparativa ou de inventario

3. **Citacao de entidades:**
   - Citar TODAS as entidades consultadas como wikilinks: `[[entity-name]]`
   - Usar wikilinks bare (nunca `[[dir/entity-name]]`)
   - Agrupar citacoes no final se houver muitas, ou inline quando natural

4. **Indicacao de fontes externas:**
   - Se fetch externo foi utilizado, indicar claramente: "Consultei tambem [fonte externa]."
   - Incluir URL original para referencia do usuario

5. **Quando nao encontrar:**
   - Dizer explicitamente: "Nao encontrei informacao sobre [X] no vault."
   - Se relevante, sugerir: "Voce pode usar `/bedrock:teach <URL>` para ingerir uma fonte sobre este assunto."
   - **NUNCA inventar informacao.** So responder com o que foi encontrado.

6. **Priorizacao na resposta (hierarquia Zettelkasten):**
   Ao montar a resposta, aplicar peso por papel Zettelkasten:
   - **Permanent notes** (actors, people, teams) — peso maximo, informacao consolidada. Apresentar como fatos atuais.
   - **Bridge notes** (topics, discussions) — peso alto, informacao contextualizada. Discussions/topics mais recentes primeiro.
   - **Index notes** (projects) — peso medio, referencia organizacional. Apontar para onde o detalhe esta.
   - **Literature notes** (sources) — peso medio, metadata de rastreabilidade.
   - **Fleeting notes** — peso baixo, informacao NAO consolidada. **SEMPRE** sinalizar com disclaimer:
     `(fonte: nota fleeting — informacao nao consolidada)`
   - Se houver informacao conflitante entre fontes, apontar a discrepancia.

7. **Deteccao de promocao de fleeting notes (criterio 3: relevancia ativa):**
   Quando uma fleeting note e referenciada na resposta por ser relevante para a query:
   - Verificar se atende criterios de promocao (ver `<base_dir>/../../entities/fleeting.md`):
     - Massa critica (>3 paragrafos com fontes)
     - Corroboracao (confirmada por permanente existente)
   - Se algum criterio e atendido, adicionar ao final da resposta:
     `> [!info] Promocao sugerida: [[fleeting-note-name]] pode ser promovida a permanent/bridge`
   - O `/bedrock:query` NAO promove automaticamente — apenas sinaliza. A promocao acontece quando
     `/bedrock:preserve` e invocado com a instrucao de promover.

### 6.2 Sugestoes pos-resposta

Quando apropriado, sugerir acoes ao usuario:

- Se informacao esta desatualizada: "O vault pode estar desatualizado sobre [X]. Considere rodar `/bedrock:teach <fonte>` para atualizar."
- Se a pergunta revelou lacunas: "Nao encontrei [Y] no vault. Se voce tem essa informacao, pode usar `/bedrock:preserve` para registrar."
- Se a pergunta e complexa e a resposta incompleta: "Para uma visao mais completa, voce pode tambem consultar [URL externa encontrada mas nao fetchada]."

---

## Regras Criticas

| Regra | Detalhe |
|---|---|
| Read-only | NUNCA escrever, editar, ou deletar arquivos. Apenas Read, Glob, Grep, Skill (fetch externo), Agent (busca paralela), e GitHub MCP (leitura) |
| Sem invencao | Responder APENAS com informacao encontrada no vault ou fontes externas consultadas. Nunca fabricar dados |
| Clarificacao antes de adivinhar | Se a pergunta e ambigua, pedir clarificacao. Nao assumir |
| Limite de 15 entidades | Nao ler mais de 15 entidades por consulta (Fase 2 + Fase 3) |
| Limite de 3 URLs externas | Nao buscar mais de 3 fontes externas por consulta |
| 1 nivel de wikilink | Nao seguir wikilinks alem do primeiro nivel |
| 1 nivel de link externo | Nao seguir links dentro de documentos externos |
| Best-effort para fetch | Se fetch externo falhar, responder com info local |
| pt-BR com termos tecnicos em ingles | Resposta sempre em portugues brasileiro |
| Wikilinks bare | `[[name]]`, nunca `[[dir/name]]` |
| Entidades consolidadas = atualizadas | Actors, people, teams nao precisam de ranking temporal |
| Discussions/topics datados = priorizar recente | Ordenar por data no filename (YYYY-MM-DD) |
| Dados sensiveis | NUNCA exibir credenciais, tokens, PANs, CVVs encontrados no vault |
| Fleeting notes com disclaimer | SEMPRE sinalizar informacao de fleeting notes com `(fonte: nota fleeting — informacao nao consolidada)` |
| Promocao como side-effect | Quando fleeting relevante atende criterios de promocao, sinalizar com callout. NAO promover automaticamente |
| Hierarquia de peso | permanent > bridge > index/literature > fleeting. Usar como diretriz, nao formula matematica |
