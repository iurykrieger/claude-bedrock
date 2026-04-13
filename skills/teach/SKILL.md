---
name: teach
description: >
  Ensina o Second Brain a reconhecer uma nova fonte de dados externa. Ingere conteudo de
  Confluence, Google Docs, CSV, Markdown local ou repositorio GitHub, extrai entidades
  (actors, discussions, projects, people, teams, topics), incorpora no vault e registra
  a fonte para re-ingestao futura.
  Use quando: "bedrock teach", "bedrock-teach", "ensinar", "ingerir fonte", "importar documento", "/bedrock:teach",
  ou quando o usuario fornecer uma URL de Confluence, Google Docs, GitHub ou um path
  de arquivo local para incorporar ao vault.
user_invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, Agent, mcp__plugin_github_github__*, mcp__plugin_atlassian_atlassian__*
---

# /bedrock:teach — Ingestao de Fontes Externas no Second Brain

## Plugin Paths

Entity definitions e templates estao no diretorio do plugin, nao na raiz do vault.
Use o "Base directory for this skill" informado na invocacao para resolver os paths:

- Entity definitions: `<base_dir>/../../entities/`
- Templates: `<base_dir>/../../templates/{type}/_template.md`
- CLAUDE.md do plugin: `<base_dir>/../../CLAUDE.md` (ja injetado automaticamente no contexto)

Onde `<base_dir>` e o path informado em "Base directory for this skill".

---

## Visao Geral

Esta skill recebe uma fonte externa (URL ou path local), extrai seu conteudo, identifica
entidades relevantes para o vault, e as incorpora — criando novas ou fundindo com existentes.
Ao final, passa a URL da fonte ao `/bedrock:preserve` que registra a proveniencia no campo `sources` de cada entidade gerada.

**Voce e um agente de execucao.** Siga as fases abaixo na ordem, sem pular etapas.

---

## Fase 1 — Detectar e Ler Fonte

### 1.1 Classificar o input

O usuario fornece um argumento. Classifique-o na seguinte ordem de prioridade:

| Input | Tipo detectado | Metodo de leitura |
|---|---|---|
| URL contendo `confluence` ou `atlassian.net` | confluence | Invocar skill `/confluence-to-markdown` passando a URL |
| URL contendo `docs.google.com` | gdoc | Invocar skill `/gdoc-to-markdown` passando a URL |
| URL contendo `github.com` | github-repo | Ver secao 1.2 abaixo |
| Path local terminando em `.csv` | csv | Ver secao 1.3 abaixo |
| Path local terminando em `.md` ou `.txt` | markdown | Use Read para ler o arquivo diretamente |
| Nenhum match acima | manual | Perguntar ao usuario: "Nao consegui identificar o tipo da fonte. Cole o conteudo ou forneca uma URL/path valido." |

Se nenhum argumento foi fornecido: perguntar ao usuario "Qual fonte deseja ingerir? Forneca uma URL (Confluence, Google Docs, GitHub) ou um path de arquivo local (.md, .csv, .txt)."

### 1.2 Leitura de repositorio GitHub

Para URLs do GitHub (ex: `https://github.com/acme-corp/billing-api`):

1. Extrair `owner/repo` da URL
2. Usar GitHub MCP diretamente (NAO via subagent — permissoes MCP nao sao herdadas):
   - `mcp__plugin_github_github__get_file_contents` → ler README.md do repo
   - `mcp__plugin_github_github__list_commits` → ultimos 10 commits
   - `mcp__plugin_github_github__list_pull_requests` → ultimos 5 PRs (state=all, sort=updated)
3. Compilar tudo em um texto markdown unico

> **Best-effort:** Se alguma chamada MCP falhar, continue com o que foi obtido. NAO bloqueie a ingestao.

### 1.2.1 Extracao semantica via graphify (GitHub repos) — OBRIGATORIO

Apos a leitura via MCP (1.2), rodar o pipeline graphify no repositorio local para extrair
entidades e relacoes semanticas (funcoes, classes, conceitos, decisoes de design).

**IMPORTANTE:** Graphify e parte OBRIGATORIA do /bedrock:teach para github-repos. NAO pular, NAO sugerir
"rodar depois", NAO apresentar como passo opcional. A persistencia de knowledge-nodes resultantes
tambem e obrigatoria — faz parte do fluxo do /bedrock:teach, nao e passo separado.

**Pre-condicoes:**
1. Extrair `repo-name` da URL (ultimo segmento: `acme-corp/billing-api` → `billing-api`)
2. Verificar se o repo existe localmente em `../<repo-name>/` (repos podem estar em subdiretorios como `../payments/<repo-name>/` — buscar recursivamente)
3. Se o repo NAO existe localmente em nenhum subdiretorio de `../`: clonar via `git clone` do GitHub e prosseguir.

**Se o repo existe localmente:**

1. Verificar se graphify esta instalado (invocar skill `/graphify` internamente nao e necessario — usar o pipeline Python diretamente):

```bash
# Detectar Python e verificar graphify
GRAPHIFY_BIN=$(which graphify 2>/dev/null)
if [ -n "$GRAPHIFY_BIN" ]; then
    PYTHON=$(head -1 "$GRAPHIFY_BIN" | tr -d '#!')
    case "$PYTHON" in
        *[!a-zA-Z0-9/_.-]*) PYTHON="python3" ;;
    esac
else
    PYTHON="python3"
fi
"$PYTHON" -c "import graphify" 2>/dev/null || "$PYTHON" -m pip install graphifyy -q 2>/dev/null || "$PYTHON" -m pip install graphifyy -q --break-system-packages 2>&1 | tail -3
mkdir -p graphify-out
"$PYTHON" -c "import sys; open('graphify-out/.graphify_python', 'w').write(sys.executable)"
```

Se a instalacao falhar: avisar "Graphify nao disponivel. Continuando com extracao textual." e prosseguir.

2. **Detect:** Detectar arquivos no repositorio local.

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.detect import detect
from pathlib import Path
result = detect(Path('../<repo-name>'))
print(json.dumps(result))
" > graphify-out/.graphify_detect.json
```

Apresentar resumo ao usuario: `Corpus: X files · ~Y words`

3. **Copiar source para dentro do vault (resolver permissoes de subagents):**

Subagents NAO conseguem ler arquivos fora do diretorio do vault. Para que a extracao
semantica funcione, copiar os arquivos do repo para `graphify-out/src/<repo-name>/`:

```bash
# Copiar source code para dentro do vault (subagents so leem dentro do vault)
rm -rf graphify-out/src/<repo-name>
mkdir -p graphify-out/src/<repo-name>
# Copiar apenas arquivos relevantes (excluir .git, bin, obj, node_modules)
rsync -a --exclude='.git' --exclude='bin' --exclude='obj' --exclude='node_modules' \
  --exclude='packages' --exclude='.vs' --exclude='TestResults' \
  <path-do-repo>/ graphify-out/src/<repo-name>/
echo "Source copiado: $(find graphify-out/src/<repo-name> -type f | wc -l) files"
```

**IMPORTANTE:** `graphify-out/` esta no `.gitignore` — os arquivos copiados nao serao commitados.

Apos copiar, re-rodar detect no path copiado para que os paths nos nodes referenciem `graphify-out/src/`:
```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.detect import detect
from pathlib import Path
result = detect(Path('graphify-out/src/<repo-name>'))
Path('graphify-out/.graphify_detect.json').write_text(json.dumps(result, indent=2))
print(f'Detect (local copy): {result.get(\"total_files\", 0)} files')
"
```

4. **Extract:** Rodar extracao AST + semantica via subagents.

**Limpeza pre-extracao (OBRIGATORIO):**

Antes de despachar subagents, limpar arquivos de extracao stale para evitar
que subagents leiam dados de runs anteriores de OUTROS repos:

```bash
# Limpar extracoes anteriores (NAO apagar graph.json — e o grafo central cross-repo)
rm -f graphify-out/.graphify_extract.json
rm -f graphify-out/.graphify_extract_*.json
rm -f graphify-out/.graphify_ast.json
echo "Limpeza pre-extracao concluida"
```

**CRITICO — Instrucoes para subagents:**

Ao despachar subagents de extracao, incluir OBRIGATORIAMENTE na prompt:
- "Voce DEVE ler arquivos APENAS de `graphify-out/src/<repo-name>/`. NAO leia `graphify-out/graph.json` nem nenhum arquivo `.graphify_extract*.json` existente. Esta e uma extracao FRESCA."
- "Salve o resultado em `graphify-out/.graphify_extract_<repo-name>.json`"

Isso evita contaminacao por nodes de outros repos que existam no graph.json de runs anteriores.

Usar subagents para extracao semantica (seguir o pipeline completo do /graphify skill:
Part A AST + Part B semantica em paralelo). Todos os paths agora apontam para
`graphify-out/src/<repo-name>/` — acessivel pelos subagents.

**Output:** O resultado da extracao deve ser salvo em arquivo **repo-especifico**:
`graphify-out/.graphify_extract_<repo-name>.json` (NAO no generico `.graphify_extract.json`).

Se multiplos subagents sao usados (ex: por modulo), cada um salva em arquivo proprio
(ex: `.graphify_extract_<repo-name>_api.json`, `.graphify_extract_<repo-name>_gateway.json`)
e o step 5 faz o merge.

**IMPORTANTE:** Se o ator ja foi processado anteriormente (verificar se `graphify-out/graph.json` existe
e contem nos com `source_file` referenciando este repo), usar `--update` para extracao incremental:
- Verificar cache via `graphify.cache.check_semantic_cache`
- Extrair apenas arquivos novos/modificados
- Isso garante que re-execucoes do /bedrock:teach no mesmo ator nao dupliquem nos

5. **Build + Cluster + Analyze:** Construir grafo, clusterizar, analisar.

**Merge de subagents (se multiplos arquivos):**

Se a extracao usou multiplos subagents (ex: por modulo), mergear os arquivos parciais
antes de construir o grafo:

```bash
$(cat graphify-out/.graphify_python) -c "
import json, glob
from pathlib import Path

all_nodes, all_edges, seen_ids = [], [], set()
for f in sorted(glob.glob('graphify-out/.graphify_extract_<repo-name>*.json')):
    data = json.loads(Path(f).read_text())
    for n in data.get('nodes', []):
        if n['id'] not in seen_ids:
            all_nodes.append(n)
            seen_ids.add(n['id'])
    all_edges.extend(data.get('edges', []))

# Deduplicate edges
edge_keys = set()
unique_edges = []
for e in all_edges:
    key = (e['source'], e['target'], e['relation'])
    if key not in edge_keys:
        unique_edges.append(e)
        edge_keys.add(key)

merged = {'nodes': all_nodes, 'edges': unique_edges}
Path('graphify-out/.graphify_extract_<repo-name>.json').write_text(json.dumps(merged, indent=2))
print(f'Merged extraction: {len(all_nodes)} nodes, {len(unique_edges)} edges')
"
```

**Construir grafo:**

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections
from graphify.export import to_json
from pathlib import Path

# Ler extracao do repo-especifico (NAO do generico .graphify_extract.json)
extraction = json.loads(Path('graphify-out/.graphify_extract_<repo-name>.json').read_text())

# Merge com graph.json existente (se houver)
existing_graph = Path('graphify-out/graph.json')
if existing_graph.exists():
    existing = json.loads(existing_graph.read_text())
    # IMPORTANTE: remover nodes do MESMO repo antes de mergear (evitar duplicatas de re-runs)
    repo_id_prefix = '<repo-name>'.replace('-', '_')
    existing['nodes'] = [n for n in existing.get('nodes', [])
                         if not n.get('id', '').startswith(repo_id_prefix)]
    existing['edges'] = [e for e in existing.get('edges', [])
                         if not e.get('source', '').startswith(repo_id_prefix)
                         and not e.get('target', '').startswith(repo_id_prefix)]
    # Adicionar nodes e edges novos
    for node in extraction.get('nodes', []):
        existing.setdefault('nodes', []).append(node)
    for edge in extraction.get('edges', []):
        existing.setdefault('edges', []).append(edge)
    merged = existing
else:
    merged = extraction

G = build_from_json(merged)
communities = cluster(G)
cohesion = score_all(G, communities)
to_json(G, communities, 'graphify-out/graph.json')

print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities')
"
```

6. **Resultado:** Armazenar os nos extraidos para uso na Fase 3:
   - `graphify-out/.graphify_extract_<repo-name>.json` — nos e edges desta extracao (arquivo repo-especifico)
   - `graphify-out/graph.json` — grafo central atualizado (merge de todos os repos)
   - Setar flag `graphify_available = true` para a Fase 3

7. **Limpeza:** Apos extracao completa, remover copia local:
```bash
rm -rf graphify-out/src/<repo-name>
```

### 1.3 Leitura de CSV

Para arquivos `.csv`:

1. Use Read para ler o arquivo
2. Se o arquivo tiver mais de 200 linhas: truncar nas primeiras 200 e avisar o usuario
3. Interpretar a primeira linha como header
4. Tratar o CSV como texto tabular — NAO assumir schema fixo
5. O conteudo sera analisado semanticamente na Fase 3

### 1.4 Resultado da Fase 1

Ao final desta fase, voce deve ter:
- **conteudo**: texto markdown da fonte (pode ser longo)
- **url_ou_path**: URL original ou path do arquivo
- **source_type**: `confluence`, `gdoc`, `github-repo`, `csv`, `markdown`, ou `manual`
- **graphify_available**: `true` se graphify foi executado com sucesso (1.2.1 ou 1.4.1)

### 1.4.1 Graphify add para fontes externas (confluence, gdoc, markdown)

Para fontes NAO-github (confluence, gdoc, markdown), adicionar o conteudo ao grafo central
via `graphify add`. Isso permite que o /bedrock:query (Part 3) faca queries cross-fonte.

**Pre-condicoes:**
- `source_type` e `confluence`, `gdoc`, ou `markdown`
- graphify esta instalado (verificar com `$(cat graphify-out/.graphify_python) -c "import graphify"`)

**Se graphify disponivel:**

1. Salvar conteudo markdown em arquivo temporario:
```bash
mkdir -p graphify-out/raw
# Salvar conteudo em graphify-out/raw/<source-slug>.md
```

2. Rodar `graphify add`:
```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.detect import detect
from graphify.extract import collect_files, extract
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.export import to_json
from pathlib import Path

# Detect + extract do arquivo novo
result = detect(Path('graphify-out/raw/<source-slug>.md'))
files = [Path('graphify-out/raw/<source-slug>.md')]

# Extracao semantica (arquivo unico — nao precisa de subagents)
# Use Read para ler o arquivo e extraia entidades como subagent unico
# O resultado segue o mesmo formato de .graphify_extract.json

# Merge com graph.json existente
existing_graph = Path('graphify-out/graph.json')
if existing_graph.exists():
    existing = json.loads(existing_graph.read_text())
    # ... merge logic (mesma da 1.2.1 step 4)
else:
    existing = extraction

G = build_from_json(existing)
communities = cluster(G)
to_json(G, communities, 'graphify-out/graph.json')
print(f'Graph updated: {G.number_of_nodes()} nodes')
"
```

3. Setar `graphify_available = true`

**Se graphify NAO disponivel:** prosseguir sem — extracao textual existente continua funcionando.
NAO bloquear a ingestao por falta de graphify.

---

## Fase 2 — Carregar Contexto do Vault

### 2.1 Ler entity definitions

Use Read para ler TODOS os arquivos de entity definitions do plugin (ver secao "Plugin Paths"):
`<base_dir>/../../entities/*.md`
Esses arquivos definem o que cada tipo de entidade e, quando criar, e como distinguir.
Internalize essas definicoes — voce vai usa-las na Fase 3 para classificar conteudo.

### 2.2 Listar entidades existentes

Use Glob para listar todos os arquivos em cada diretorio de entidades (excluindo `_template.md`):
- `actors/*.md`
- `people/*.md`
- `teams/*.md`
- `topics/*.md`
- `discussions/*.md`
- `projects/*.md`
- `fleeting/*.md`
- `fleeting/*.md`

Para cada arquivo encontrado:
- Extraia o filename sem extensao (ex: `billing-api`)
- Use Read para extrair o campo `name` do frontmatter YAML
- Armazene: `{filename, name, tipo}` para matching na Fase 3

Reporte: "Fase 2: N entity definitions carregadas, M entidades existentes catalogadas."

---

## Fase 3 — Analisar Conteudo e Extrair Entidades

### 3.1 Identificar entidades existentes mencionadas

Para cada entidade catalogada na Fase 2, verifique se o filename OU o name aparece no conteudo:

**Regras de match:**
- Normalize para comparacao: lowercase, sem acentos, sem hifens
- Match parcial e aceitavel para nomes compostos (ex: "billing api" match "billing-api")
- NAO matchar substrings de 3 letras ou menos (ex: "api" NAO match "billing-api")
- NAO matchar palavras genericas (ex: "company", "service", "system")

Para cada match, registre:
- Tipo (actor, person, team, topic, discussion, project)
- Filename (para wikilink)
- Acao: `update`
- Info extraida: trecho do conteudo onde aparece

### 3.1.1 Classificacao Zettelkasten do conteudo

Para cada trecho de conteudo analisado, classificar por maturidade antes de extrair entidades:

**Conteudo consolidado (→ permanent/bridge):**
- Dados concretos: nomes de repositorios, nomes completos de pessoas, datas especificas, decisoes explicitas
- Informacao auto-contida: compreensivel sem contexto externo
- Atende criterios de completude de pelo menos 1 entity definition (ver secao "Criterio de Completude" nas entity definitions do plugin)

**Conteudo em formacao (→ fleeting):**
- Mencoes vagas: "alguem mencionou...", "parece que...", "talvez..."
- Fragmentos sem contexto: nomes parciais, ideias soltas, hipoteses
- TODOs genericos sem responsavel ou prazo
- Informacao que NAO atende criterios de completude de nenhum tipo

**Regra:** ao classificar entidades para a lista da Fase 3, incluir o campo `type: fleeting` para conteudo em formacao.
O `/bedrock:preserve` faz a validacao final via Fase 1.3 (Classificacao Zettelkasten).

### 3.1.2 Classificar nos do graphify (se graphify_available)

Se `graphify_available = true` (Fase 1.2.1 ou 1.4.1), ler `graphify-out/.graphify_extract_<repo-name>.json`
e classificar cada no extraido pelo graphify:

1. **Ler os nos extraidos:**
```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
extract = json.loads(Path('graphify-out/.graphify_extract_<repo-name>.json').read_text())
print(json.dumps({'nodes': len(extract.get('nodes', [])), 'edges': len(extract.get('edges', []))}, indent=2))
"
```

2. **Para cada no com `file_type: code`** (funcoes, classes, modulos, endpoints):
   - Classificar como `type: knowledge-node`
   - Preencher campos obrigatorios:
     - `name`: usar `label` do no graphify
     - `graphify_node_id`: usar `id` do no graphify
     - `actor`: inferir a partir do `source_file` ou do repo que foi processado
     - `node_type`: inferir a partir do contexto (function, class, module, interface, endpoint)
     - `source_file`: usar `source_file` do no graphify
     - `confidence`: usar `confidence` do edge mais forte conectado ao no (EXTRACTED > INFERRED > AMBIGUOUS)
     - `description`: gerar descricao em pt-BR baseada no label e contexto
   - Mapear edges do graphify para campo `relations` (wikilinks para outros knowledge-nodes)
   - Adicionar na lista de entidades com `action: create` (ou `update` se `graphify_node_id` ja existe no vault)

3. **Para cada no com `file_type: document` ou `file_type: paper`** (conceitos, decisoes):
   - **NAO classificar automaticamente como knowledge-node**
   - Usar entity definitions do plugin (ver secao "Plugin Paths") para classificar:
     - Se descreve uma decisao de arquitetura ampla → `type: topic`
     - Se descreve uma reuniao ou debate → `type: discussion`
     - Se e um conceito em formacao → `type: fleeting`
     - Se descreve algo especifico de um ator → `type: knowledge-node`
   - Aplicar regras de Classificacao Zettelkasten (3.1.1)
   - Consultar secoes "Quando criar", "Quando NAO criar", "Como distinguir" de cada entity definition

4. **Edges do graphify → relacoes:**
   - Para cada edge entre nos classificados, adicionar na lista de `relations` do input estruturado
   - Edges `EXTRACTED` → relacao certa, incluir
   - Edges `INFERRED` → relacao provavel, incluir com nota
   - Edges `AMBIGUOUS` → omitir (serao revistos no /bedrock:compress)

5. **Migracao automatica de ator para pasta:**
   - Se knowledge-nodes vao ser criados para um ator que ainda e arquivo flat:
     - Migrar `actors/<name>.md` → `actors/<name>/<name>.md` (via `git mv`)
     - Criar `actors/<name>/nodes/`
     - Adicionar secao "Knowledge Nodes" ao corpo do ator

6. **Filtrar nos relevantes para persistencia:**
   - Selecionar os top ~50 nos por relevancia (god nodes, classes de servico, controllers, interfaces publicas)
   - Criterios de filtragem: degree > media, ou label contem "Service", "Controller", "Client", "Factory", "Handler", "Mapper"
   - Nos de teste (labels com "Tests", "Test", "Builder") sao EXCLUIDOS — nao persistir testes como knowledge-nodes
   - Nos triviais (getters, setters, DTOs simples) sao EXCLUIDOS
   - Os nos filtrados serao incluidos na lista de entidades da Fase 3.3 como `type: knowledge-node`

**IMPORTANTE:** A persistencia de knowledge-nodes e OBRIGATORIA — faz parte do fluxo do /bedrock:teach.
NAO apresentar como "proximo passo sugerido". Os knowledge-nodes filtrados sao incluidos na
lista de entidades para confirmacao do usuario (Fase 3.3) e delegados ao /bedrock:preserve (Fase 4)
junto com as demais entidades.

Reportar: "Graphify: N nos de codigo extraidos, M filtrados para persistencia (→ knowledge-nodes), P edges."

### 3.2 Identificar entidades NOVAS a criar

Analise o conteudo procurando trechos que descrevem algo que NAO existe no vault mas
se encaixa numa definicao de entidade. Para cada candidato:

1. Consulte a secao "Quando criar" da definicao correspondente → criterios positivos
2. Consulte a secao "Quando NAO criar" → criterios de exclusao
3. Se ambiguo, consulte "Como distinguir de outros tipos" → desambiguacao
4. Se o candidato passa nos criterios: registre como entidade nova

Para cada entidade nova, registre:
- Tipo (actor, person, team, topic, discussion, project)
- Nome canonico sugerido (repo name para actors, nome completo para persons, etc.)
- Acao: `create`
- Info extraida: trecho do conteudo que justifica a criacao

### 3.3 Apresentar ao usuario para confirmacao

**OBRIGATORIO:** Antes de criar/atualizar qualquer entidade, apresente a lista completa:

```
## Entidades detectadas

| # | Tipo | Nome | Acao | Info extraida | Fonte |
|---|---|---|---|---|---|
| 1 | actor | billing-api | update | Mencionado como dependencia do novo fluxo | textual |
| 2 | discussion | 2026-04-04-planning-q2 | create | Ata de reuniao com decisoes sobre migracao | textual |
| 3 | person | alice-smith | create | Mencionado como DRI do projeto X | textual |
| 4 | knowledge-node | ProcessTransaction | create | Funcao de orquestracao do fluxo de autorizacao | graphify |
| 5 | knowledge-node | KafkaEventPublisher | create | Publicacao de eventos Kafka | graphify |

Confirma? (s/n, ou edite a lista removendo linhas indesejadas)

> **Nota:** Entidades com fonte "graphify" foram extraidas via analise semantica do repositorio.
> Entidades com fonte "textual" foram extraidas via pattern matching no conteudo.
```

- Se o usuario confirma: prossiga para Fase 4
- Se o usuario edita: ajuste a lista conforme instrucoes
- Se o usuario cancela: encerre com "Ingestao cancelada. Nenhuma entidade modificada."

---

## Fase 4 — Delegar Entidades ao /bedrock:preserve

Todas as entidades confirmadas pelo usuario (Fase 3) sao delegadas ao `/bedrock:preserve`.
O `/bedrock:teach` NAO cria nem atualiza entidades diretamente — essa responsabilidade e do `/bedrock:preserve`.

### 4.1 Compilar lista estruturada

Monte a lista de entidades no formato aceito pelo `/bedrock:preserve`:

```yaml
entities:
  - type: discussion
    name: "2026-04-05-planning-q2"
    action: create
    content: "trecho relevante do conteudo extraido na Fase 3..."
    relations:
      actors: ["actor-slug-1"]
      people: ["person-slug-1"]
    source: "<source_type da Fase 1>"
    source_url: "<url_ou_path da Fase 1>"
    source_type: "<source_type da Fase 1>"
  - type: actor
    name: "billing-api"
    action: update
    content: "novo contexto extraido na Fase 3..."
    source: "<source_type da Fase 1>"
    source_url: "<url_ou_path da Fase 1>"
    source_type: "<source_type da Fase 1>"
```

**Regras de compilacao:**
- `type` e `name`: extraidos da Fase 3 (lista confirmada pelo usuario)
- `action`: `create` ou `update` conforme identificado na Fase 3
- `content`: trecho do conteudo da fonte que justifica a entidade
- `relations`: inferir relacoes entre entidades da lista (se A menciona B, incluir B nas relations de A)
- `source`: usar o `source_type` detectado na Fase 1 (confluence, gdoc, github-repo, csv, markdown, manual). Para knowledge-nodes, usar `"graphify"`
- `source_url`: URL ou path da fonte externa (campo `url_ou_path` da Fase 1). O `/bedrock:preserve` usa este valor para popular o campo `sources` no frontmatter da entidade
- `source_type`: tipo da fonte externa (mesmo valor de `source`). O `/bedrock:preserve` usa este valor para o campo `sources[].type`
- `metadata`: incluir campos adicionais de frontmatter quando disponiveis (ex: `status`, `role`, `team`)

**Regras adicionais para knowledge-nodes (fonte graphify):**
- `type`: `knowledge-node`
- `metadata.graphify_node_id`: id do no no graphify (ex: `billing_api_processTransaction`)
- `metadata.actor`: wikilink do ator pai (ex: `"[[billing-api]]"`)
- `metadata.node_type`: `function`, `class`, `module`, `concept`, `decision`, `interface`, `endpoint`
- `metadata.source_file`: caminho relativo no repo do ator
- `metadata.confidence`: `EXTRACTED`, `INFERRED`, ou `AMBIGUOUS`
- `relations.knowledge_nodes`: wikilinks para outros knowledge-nodes conectados via edges do graphify

### 4.2 Invocar /bedrock:preserve

Use a tool Skill para invocar `/bedrock:preserve` passando a lista estruturada como argumento.

O `/bedrock:preserve` cuida de:
- Matching textual com entidades existentes
- Criacao de novas entidades seguindo templates
- Atualizacao de entidades existentes (merge/append-only)
- Vinculacao bidirecional (wikilinks)
- Git commit das entidades

### 4.3 Aguardar resultado

O `/bedrock:preserve` retorna:
- Lista de entidades criadas/atualizadas
- Commit hash (se houve commit)
- Eventuais erros ou avisos

Registre o resultado para uso no relatorio final (Fase 5).

---

## Fase 5 — Relatorio

O `/bedrock:preserve` ja fez commit das entidades (incluindo o campo `sources` populado com a URL da fonte).
O `/bedrock:teach` NAO faz commit separado — a proveniencia e registrada dentro de cada entidade pelo `/bedrock:preserve`.

Apresente ao usuario:

```
## /bedrock:teach — Relatorio

### Fonte ingerida
- **Tipo:** <source_type>
- **URL/Path:** <url>

### Entidades processadas (via /bedrock:preserve)
| Tipo | Nome | Acao |
|---|---|---|
| discussion | 2026-04-04-planning-q2 | create |
| actor | billing-api | update |
| person | alice-smith | create |

### Proveniencia
Cada entidade acima recebeu no campo `sources` do frontmatter:
- url: <url_ou_path>
- type: <source_type>
- synced_at: <data de hoje>

### Git
- Commit: <hash do /bedrock:preserve ou "nenhuma entidade">
- Push: sucesso / falhou (motivo)

### Sugestoes
- [lista de entidades mencionadas no conteudo mas nao criadas, se houver]
- [recomendacoes de re-ingestao futura, se aplicavel]
```

---

## Regras Criticas

| Regra | Detalhe |
|---|---|
| Confirmacao obrigatoria | SEMPRE apresentar lista de entidades ao usuario ANTES de criar/atualizar (Fase 3.3) |
| Entity definitions sao o manual | Consultar entity definitions do plugin (ver "Plugin Paths") para classificar conteudo |
| Delegar ao /bedrock:preserve | TODAS as entidades sao persistidas via `/bedrock:preserve` — teach NAO cria/atualiza inline |
| Proveniencia via source_url | SEMPRE incluir `source_url` e `source_type` no input delegado ao /bedrock:preserve. O /bedrock:preserve popula o campo `sources` no frontmatter |
| Frontmatter keys em ingles | `type`, `name`, `updated_at`, etc. Valores em pt-BR |
| Wikilinks bare | `[[name]]`, nunca `[[dir/name]]` |
| Wikilinks sempre kebab-case | `[[charge-service]]`, nunca `[[ChargeService]]` ou `[[chargeService]]`. Ao gerar wikilinks para knowledge-nodes, converter camelCase/PascalCase para kebab-case. Ex: `ProcessTransaction` → `[[process-transaction]]`, `KafkaEventPublisher` → `[[kafka-event-publisher]]` |
| Append-only para people/teams/topics | NUNCA deletar conteudo existente no corpo |
| Actors podem ser modificados | Merge livre no corpo e frontmatter |
| Best-effort para fontes externas | Se MCP falhar, continue com o que foi obtido |
| MCP no contexto principal | NAO usar subagents para chamadas GitHub/Atlassian MCP |
| CSV truncado em 200 linhas | Avisar o usuario se o arquivo for maior |
| Maximo 2 tentativas de push | Apos isso, abortar e informar |
| Dados sensiveis | NUNCA incluir credenciais, tokens, senhas, PANs, CVVs |
