---
name: compress
description: >
  Varre o vault, identifica conteudo duplicado ou fragmentado entre entidades do mesmo tipo,
  monta proposta de unificacao em formato tabela, e executa apos confirmacao do usuario.
  Gera health report (wikilinks unresolved, entidades orfas, desatualizadas).
  Use quando: "bedrock compress", "bedrock-compress", "limpar vault", "consolidar vault", "unificar entidades",
  "encontrar duplicacoes", "/bedrock:compress".
user_invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
---

# /bedrock:compress — Consolidacao e Health Check do Vault

## Plugin Paths

Entity definitions e templates estao no diretorio do plugin, nao na raiz do vault.
Use o "Base directory for this skill" informado na invocacao para resolver os paths:

- Entity definitions: `<base_dir>/../../entities/`
- Templates: `<base_dir>/../../templates/{type}/_template.md`
- CLAUDE.md do plugin: `<base_dir>/../../CLAUDE.md` (ja injetado automaticamente no contexto)

Onde `<base_dir>` e o path informado em "Base directory for this skill".

---

## Visao Geral

Esta skill varre todas as entidades do vault, detecta conteudo semanticamente duplicado
ou fragmentado DENTRO do mesmo tipo de entidade, propoe unificacao ao usuario, e executa
apos confirmacao explicita. Tambem gera um health report do vault.

**Voce e um agente de execucao.** Siga as fases abaixo na ordem, sem pular etapas.

**Regras criticas:**
- **NUNCA** executar mudancas sem confirmacao explicita do usuario
- **NUNCA** comparar entidades de tipos diferentes (actor vs topic, etc.)
- **NUNCA** deletar entidades — apenas consolidar conteudo
- **NUNCA** alterar frontmatter (exceto `updated_at` e `updated_by`)
- **NUNCA** alterar templates (`_template.md`), conventions, ou patterns
- **NUNCA** remover wikilinks existentes
- People/Teams/Topics: **append-only** — adicionar nota de consolidacao, nunca deletar conteudo
- Actors: **merge livre** — pode editar corpo livremente

---

## Fase 0 — Sincronizar o Vault

Execute:
```bash
git pull --rebase origin main
```

Se falhar:
- Sem remote: avisar "Nenhum remote configurado. Trabalhando localmente." e prosseguir.
- Conflito: `git rebase --abort` e avisar o usuario. NAO prosseguir sem resolver.

---

## Fase 1 — Varrer o Vault

Para cada tipo de entidade (`actors`, `people`, `teams`, `topics`, `discussions`, `projects`, `fleeting`):

1. Listar todos os arquivos `.md` no diretorio, **excluindo `_template.md` e `_template_node.md`**
   - Para actors: incluir tanto `actors/*.md` (flat) quanto `actors/*/*.md` (pasta)
   - Incluir knowledge-nodes: `actors/*/nodes/*.md`
2. Para cada entidade, ler frontmatter + corpo
3. Para knowledge-nodes: extrair adicionalmente `graphify_node_id` e `actor` do frontmatter
4. Extrair **claims** — afirmacoes factuais distintas:
   - Cada bullet point, linha de tabela, ou paragrafo e um claim potencial
   - **Ignorar** secoes estruturais vazias (placeholders do template)
   - **Ignorar** secao "Expected Bidirectional Links" (referencia, nao conteudo)
   - **Ignorar** secao "Atividade Recente" (temporal, nao factual)
   - **Ignorar** callouts obrigatorios padrao (`[!warning] Deprecated`, `[!danger] PCI Scope`, etc.)

**Output:** mapa `tipo → [{entidade, claims[]}]`

### Otimizacao para vaults grandes

Se o vault tiver mais de 100 entidades em um tipo, processar em batches de 30.
Usar subagents via Agent tool para paralelizar leitura por tipo de entidade.

---

## Fase 1.5 — Integridade do Grafo (graphify)

Se `graphify-out/graph.json` existe, verificar consistencia entre o grafo e o vault.
Se NAO existe: pular esta fase e reportar "Graph.json nao encontrado. Rode /bedrock:teach para gerar." no health report.

### 1.5.1 Carregar dados

```bash
$(cat graphify-out/.graphify_python 2>/dev/null || echo python3) -c "
import json
from pathlib import Path
g = json.loads(Path('graphify-out/graph.json').read_text())
nodes = g.get('nodes', [])
code_nodes = [n for n in nodes if n.get('file_type') == 'code']
print(f'{len(nodes)} nos total, {len(code_nodes)} nos de codigo')
"
```

Coletar:
- `graph_nodes`: todos os nos do graph.json com `file_type: code` e seus `id`
- `vault_knowledge_nodes`: todos os knowledge-nodes em `actors/*/nodes/*.md` com seus `graphify_node_id`
- `vault_actors`: lista de atores (pastas em `actors/` que contem `<name>.md`)

### 1.5.2 Verificacao A — Knowledge-nodes orfaos (ator removido)

Para cada knowledge-node encontrado na Fase 1:
1. Extrair `actor` do frontmatter (wikilink para o ator pai)
2. Resolver o ator: verificar se `actors/<actor-name>/<actor-name>.md` existe
3. Se NAO existe: marcar como **orfao (ator removido)**

### 1.5.3 Verificacao B — Knowledge-nodes orfaos (no removido do grafo)

Para cada knowledge-node com `graphify_node_id` definido:
1. Verificar se o `graphify_node_id` existe em `graph_nodes` (IDs do graph.json)
2. Se NAO existe: marcar como **orfao (no removido do grafo)** — provavelmente o codigo
   foi deletado no repositorio e o /bedrock:teach re-processou sem gerar este no

### 1.5.4 Verificacao C — Nos do grafo nao persistidos

Para cada no em `graph_nodes` (nos com `file_type: code` no graph.json):
1. Verificar se existe knowledge-node em `vault_knowledge_nodes` com `graphify_node_id` correspondente
2. Se NAO existe: registrar como **no nao persistido** — o /bedrock:teach extraiu este no mas o
   /bedrock:preserve nao o gravou no vault (pode indicar que /bedrock:teach nao completou a fase de preservacao)

### 1.5.5 Verificacao D — graph.json stale

1. Verificar data de modificacao de `graphify-out/graph.json`
```bash
stat -f "%Sm" -t "%Y-%m-%d" graphify-out/graph.json 2>/dev/null || stat -c "%y" graphify-out/graph.json 2>/dev/null | cut -d' ' -f1
```
2. Se a data e anterior a 30 dias: marcar como **stale**
3. Sugerir: "Graph.json desatualizado (>30 dias). Rode /bedrock:teach ou /sync para atualizar."

### 1.5.6 Resultado

Armazenar contadores para o health report:
- `graph_exists`: sim/nao
- `graph_total_nodes`: N
- `vault_knowledge_nodes_count`: M
- `nodes_synced`: nos presentes tanto no grafo quanto no vault
- `orphan_actor_removed`: knowledge-nodes cujo ator nao existe
- `orphan_node_removed`: knowledge-nodes cujo graphify_node_id nao esta no grafo
- `nodes_not_persisted`: nos do grafo sem knowledge-node correspondente
- `graph_updated_at`: data de modificacao do graph.json
- `graph_stale`: sim/nao

---

## Fase 2 — Detectar Duplicacao

Para cada tipo de entidade, comparar claims **DENTRO do mesmo tipo** (NUNCA cross-type).

**Knowledge-nodes:** comparar DENTRO do mesmo ator (knowledge-nodes de atores diferentes nao sao
comparados entre si, pois podem representar funcoes legitimamente similares em repos distintos).
Dois knowledge-nodes do mesmo ator com descricoes semanticamente identicas → cluster.

### 2.1 Duplicacao semantica
Dois claims que dizem a mesma coisa com palavras diferentes.
Exemplo:
- Actor A: "API de pagamentos com cartao"
- Actor B: "Servico que processa pagamentos de cartao de credito"

### 2.2 Fragmentacao
Informacao sobre o mesmo assunto dispersa em 3+ entidades sem consolidacao.
Exemplo:
- Actor A menciona "usa Kafka para eventos"
- Actor B menciona "publica eventos no Kafka"
- Actor C menciona "consome eventos Kafka de B"
- Nenhuma entidade consolida o fluxo completo

### 2.3 Gerar clusters

Para cada duplicacao encontrada, criar um cluster:

```yaml
cluster:
  id: N
  tipo: actor | person | team | topic | discussion | project
  descricao: "descricao do conteudo duplicado"
  entidades:
    - nome: "entity-a"
      claim: "texto do claim duplicado"
    - nome: "entity-b"
      claim: "texto do claim duplicado"
  entidade_principal: "entity-a"  # a mais completa/relevante
  conteudo_unificado: "texto consolidado"
```

**Criterios para escolher a entidade principal:**
- Mais completa (mais claims, mais detalhes)
- Mais recente (`updated_at` mais recente)
- Mais conectada (mais wikilinks inbound/outbound)

Se nenhuma duplicacao for encontrada, informar o usuario e pular para o Health Report (Fase 4.2).

---

## Fase 3 — Montar Proposta

Para cada cluster, apresentar ao usuario:

```markdown
### Cluster N: <descricao do conteudo duplicado>

**Tipo:** <tipo da entidade>

**Entidades envolvidas:**
| Entidade | Claim |
|---|---|
| [[entity-a]] | "descricao X do servico" |
| [[entity-b]] | "servico faz X" |

**Proposta:**
- **Manter em:** [[entity-a]] (entidade mais completa/relevante)
- **Conteudo unificado:** "descricao consolidada..."
- **Remover de / Consolidar em:** [[entity-b]]

**Impacto:** N entidades, M claims
```

### Resumo da proposta

Apos listar todos os clusters:

```markdown
## Resumo

| # | Descricao | Tipo | Entidades | Claims |
|---|---|---|---|---|
| 1 | ... | actor | 2 | 3 |
| 2 | ... | topic | 3 | 5 |

**Total:** N clusters, M entidades, P claims

Confirma a execucao? (sim/nao)
```

### Proposta de limpeza de orfaos do grafo (se Fase 1.5 encontrou orfaos)

Se a Fase 1.5 identificou knowledge-nodes orfaos ou nos nao persistidos, apresentar proposta adicional:

```markdown
## Orfaos do Grafo

### Knowledge-nodes orfaos (ator removido)
| # | Knowledge-node | Ator (removido) | Acao proposta |
|---|---|---|---|
| 1 | [[node-name]] | [[actor-name]] | `git rm actors/<actor>/nodes/<node>.md` |

### Knowledge-nodes orfaos (no removido do grafo)
| # | Knowledge-node | graphify_node_id | Acao proposta |
|---|---|---|---|
| 1 | [[node-name]] | `id_no_grafo` | `git rm actors/<actor>/nodes/<node>.md` |

### Nos do grafo nao persistidos
| # | Node ID | Label | Acao proposta |
|---|---|---|---|
| 1 | `node_id` | Node Label | Rodar `/bedrock:teach` no ator correspondente |

Confirma a limpeza de orfaos? (sim/nao/parcial)
```

**IMPORTANTE:** A limpeza de orfaos e SEPARADA da consolidacao de duplicatas.
O usuario pode confirmar uma sem a outra. Permitir confirmacao parcial por ator
(ex: "limpar orfaos so do billing-api").

**PARAR AQUI e aguardar confirmacao do usuario.**

Se o usuario disser "nao" ou pedir ajustes, ajustar a proposta e reapresentar.
Se o usuario confirmar parcialmente (ex: "so os clusters 1 e 3"), executar apenas os confirmados.

---

## Fase 4 — Executar

### 4.1 Consolidar entidades

Para cada cluster confirmado pelo usuario:

#### Actors (merge livre)
1. Ler a entidade principal (`entity-a`)
2. Incorporar o conteudo unificado no corpo da entidade principal
3. Ler a entidade secundaria (`entity-b`)
4. Remover o claim duplicado do corpo da entidade secundaria
5. Atualizar frontmatter de ambas:
   ```yaml
   updated_at: <data de hoje YYYY-MM-DD>
   updated_by: "compress@agent"
   ```

#### People / Teams / Topics (append-only)
1. Ler a entidade principal (`entity-a`)
2. Adicionar o conteudo unificado como nova secao ou complemento no corpo
3. Ler a entidade secundaria (`entity-b`)
4. **NAO deletar** o conteudo original. Adicionar callout apos o claim duplicado:
   ```markdown
   > [!info] Conteudo consolidado em [[entity-a]]
   > Este conteudo foi consolidado na entidade principal. Consulte [[entity-a]] para a versao mais completa.
   ```
5. Atualizar frontmatter de ambas:
   ```yaml
   updated_at: <data de hoje YYYY-MM-DD>
   updated_by: "compress@agent"
   ```

#### Discussions / Projects (append-only)
Seguir a mesma regra de People/Teams/Topics: append-only com callout de consolidacao.

#### Knowledge-nodes orfaos (se confirmado pelo usuario)

Para cada knowledge-node orfao confirmado (ator removido ou no removido do grafo):
1. Executar `git rm actors/<actor>/nodes/<node-name>.md`
2. Se a pasta `actors/<actor>/nodes/` ficou vazia: manter (nao deletar pasta vazia)
3. Remover referencia do knowledge-node na secao "Knowledge Nodes" do ator pai (se ator existe)
4. Atualizar `updated_at` e `updated_by` do ator pai (se tocado)

**IMPORTANTE:** Knowledge-nodes sao a unica entidade que pode ser deletada via `git rm`.
Todas as outras entidades seguem a regra de consolidacao (nunca deletar).
O graph.json NAO e modificado — se nos precisam ser removidos do grafo, rodar /bedrock:teach com `--update`.

### 4.2 Gerar Health Report

Aproveitar a varredura completa do vault para gerar:

#### Wikilinks unresolved
- Varrer todos os arquivos de entidade
- Extrair todos os wikilinks `[[nome]]`
- Verificar se existe arquivo correspondente em algum diretorio de entidade
- Listar os que nao resolvem

#### Entidades orfas
- Entidades sem nenhum wikilink inbound (nenhuma outra entidade aponta para ela)
- Verificar via Grep em todos os arquivos de entidade

#### Entidades desatualizadas
- Entidades com `updated_at` mais antigo que 60 dias a partir da data atual
- Extrair `updated_at` do frontmatter de cada entidade

#### Fleeting notes estagnadas
- Fleeting notes com status `raw` ha mais de 30 dias (baseado em `captured_at`)
- Para cada fleeting note estagnada, verificar se atende criterios de promocao (ver `entities/fleeting.md`):
  - **Massa critica:** >3 paragrafos com fontes verificaveis → sugerir promocao
  - **Corroboracao:** informacao confirmada por permanente existente → sugerir promocao
  - Se nenhum criterio atendido → sugerir arquivamento (`status: archived`)
- Incluir no health report com acoes sugeridas:
  ```
  | Fleeting Note | Dias em raw | Acao sugerida |
  |---|---|---|
  | [[2026-03-05-novo-servico]] | 35 | Promover (massa critica) |
  | [[2026-03-01-ideia-vaga]] | 39 | Arquivar (sem criterio de promocao) |
  ```

#### Integridade do Grafo (se graphify-out/graph.json existe)

Usando os dados coletados na Fase 1.5, gerar a secao de integridade:

```markdown
## Integridade do Grafo

| Metrica | Valor |
|---|---|
| Graph.json existe | sim/nao |
| Nos no graph.json | N |
| Knowledge-nodes no vault | M |
| Nos sincronizados (grafo <-> vault) | X |
| Knowledge-nodes orfaos (ator removido) | Y |
| Knowledge-nodes orfaos (no removido do grafo) | Z |
| Nos do grafo nao persistidos | W |
| Graph.json atualizado em | YYYY-MM-DD |
| Graph.json stale (>30d) | sim/nao |
```

Se graph.json nao existe: reportar apenas "Graph.json nao encontrado. Rode /bedrock:teach para gerar."
Se graph.json existe mas nao ha orfaos: reportar todos os contadores com zeros.
Se graph.json e stale: adicionar aviso "Sugestao: rode /bedrock:teach ou /sync para atualizar o grafo."

**Filtro:** Reportar apenas achados acionaveis. Ignorar:
- Wikilinks para entidades que sao referencia valida mas ainda nao criadas (aceitavel no Obsidian)
- Templates e arquivos de configuracao

---

## Fase 5 — Git Commit + Relatorio

### 5.1 Commit

```bash
git add actors/ people/ teams/ topics/ discussions/ projects/ fleeting/
# Mensagem inclui knowledge-nodes orfaos removidos (se houver)
git commit -m "vault: compress N entities [fonte: compress]"
# Se knowledge-nodes orfaos foram removidos, usar:
# git commit -m "vault: compress N entities, remove M knowledge-nodes orfaos [fonte: compress]"
```

Onde N = numero total de entidades tocadas.

### 5.2 Push

```bash
git push origin main
```

Se falhar:
```bash
git pull --rebase origin main && git push origin main
```

Max 2 tentativas. Se falhar apos 2: avisar o usuario que o push falhou.

### 5.3 Relatorio Final

Apresentar ao usuario:

```markdown
## /bedrock:compress — Relatorio

### Clusters processados
| # | Descricao | Tipo | Entidades | Claims unificados |
|---|---|---|---|---|
| 1 | ... | actor | 2 | 3 |
| 2 | ... | topic | 3 | 5 |

**Total:** N clusters, M entidades, P claims unificados

### Health Report
| Check | Count | Detalhes |
|---|---|---|
| Wikilinks unresolved | N | [[link1]], [[link2]], ... |
| Entidades orfas | N | [[entity1]], [[entity2]], ... |
| Entidades desatualizadas (>60d) | N | [[entity3]], [[entity4]], ... |

### Git
- Commit: `vault: compress N entities [fonte: compress]`
- Push: sucesso / falhou (motivo)
```

Se nenhum cluster foi processado (nao havia duplicacao ou usuario recusou tudo),
apresentar apenas o Health Report.

---

## Tratamento de Erros

| Situacao | Acao |
|---|---|
| Vault vazio (sem entidades) | Informar "Nenhuma entidade encontrada no vault." e encerrar |
| Nenhuma duplicacao encontrada | Informar e pular para Health Report |
| Usuario recusa todos os clusters | Informar e pular para Health Report |
| Erro ao ler entidade | Pular entidade, avisar no relatorio |
| Conflito no git push | Rebase + retry (max 2). Se falhar: avisar usuario |
| Entidade sem frontmatter | Pular entidade, avisar no relatorio |
