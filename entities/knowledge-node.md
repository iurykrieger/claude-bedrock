# Entity: Knowledge Node

> Fonte de verdade para campos obrigatorios: `actors/_template_node.md`

## O que e

Um **knowledge-node** e uma unidade granular de conhecimento extraida automaticamente pelo graphify a partir do codigo-fonte ou documentacao de um ator. Representa funcoes, classes, modulos, conceitos, decisoes, interfaces ou endpoints que foram identificados pela analise semantica (AST + LLM) do repositorio.

Knowledge-nodes sao sub-entidades de atores — cada knowledge-node pertence a exatamente um ator e vive dentro da pasta do ator em `actors/<actor-name>/nodes/`. Eles formam a camada de detalhamento fino do grafo de conhecimento, conectando o vault a informacoes que existem no codigo mas nao seriam capturadas por descricoes de alto nivel.

## Quando criar

- O graphify extraiu um no do repositorio de um ator (funcao, classe, modulo, interface, endpoint) com relevancia semantica
- O graphify extraiu um conceito ou decisao de arquitetura a partir de documentacao vinculada a um ator
- O no tem `confidence` EXTRACTED ou INFERRED (nao puramente AMBIGUOUS)
- O ator correspondente ja existe no vault

## Quando NAO criar

- O no e trivial (getter/setter generico, boilerplate, auto-generated code) — filtrar por relevancia
- O no ja existe como outra entidade no vault (ex: um conceito que ja e um topic)
- O ator correspondente nao existe no vault — criar o ator primeiro
- O no tem confidence AMBIGUOUS sem edges que o conectem a outros nos — informacao isolada sem valor
- O conteudo e sensivel (credenciais, tokens, PANs, CVVs) — nunca persistir dados sensiveis

## Como distinguir de outros tipos

| Parece ser... | Mas e... | Diferenca-chave |
|---|---|---|
| Knowledge-node | Topic | Se o conteudo e uma decisao de arquitetura ampla que afeta multiplos atores, e um topic. Se e especifico de uma funcao/classe de um ator, e knowledge-node |
| Knowledge-node | Actor | Se tem repositorio e deploy independente, e ator. Knowledge-nodes sao partes internas de um ator |
| Knowledge-node | Fleeting | Se veio do graphify com confidence EXTRACTED/INFERRED e tem `graphify_node_id`, e knowledge-node. Se e uma ideia solta sem vinculo ao grafo, e fleeting |
| Knowledge-node | Discussion | Se descreve uma decisao tomada em reuniao/debate, e discussion. Se descreve uma decisao de design encontrada no codigo, e knowledge-node |

## Campos obrigatorios (frontmatter)

| Campo | Tipo | Descricao |
|---|---|---|
| `type` | string | Sempre `"knowledge-node"` |
| `name` | string | Nome legivel do no (ex: `"ProcessTransaction"`, `"KafkaEventPublisher"`) |
| `aliases` | array | Nomes alternativos (min 1). Ex: `["Process Transaction", "processTransaction"]` |
| `actor` | wikilink | `"[[actor-name]]"` — ator pai ao qual este no pertence |
| `node_type` | string | `function`, `class`, `module`, `concept`, `decision`, `interface`, `endpoint` |
| `source_file` | string | Caminho relativo no repo do ator (ex: `src/Controllers/PaymentController.cs`) |
| `description` | string | Descricao em pt-BR da funcao/papel deste no |
| `graphify_node_id` | string | ID unico do no no graph.json (ex: `billing_api_processTransaction`) |
| `confidence` | string | `EXTRACTED`, `INFERRED`, ou `AMBIGUOUS` — nivel de confianca da extracao |
| `updated_at` | date | YYYY-MM-DD |
| `updated_by` | string | Quem atualizou |
| `tags` | array | Tags hierarquicas: `[type/knowledge-node]` + `domain/*` herdado do ator |

### Campos opcionais

| Campo | Tipo | Descricao |
|---|---|---|
| `relations` | array | Wikilinks para outros knowledge-nodes ou entidades relacionadas |
| `source_location` | string | Linha ou range no source_file (ex: `L42-L85`) |

## Papel Zettelkasten

**Classificacao:** extensao de permanent note (sub-entidade de actor)
**Proposito no grafo:** Representar detalhes granulares de implementacao de atores — funcoes, classes, decisoes de design — que enriquecem o grafo de conhecimento sem poluir as permanent notes de alto nivel.

### Regras de Linking

**Links estruturais (frontmatter):** `actor` (wikilink para o ator pai). Define a hierarquia — todo knowledge-node pertence a exatamente um ator.
**Links semanticos (corpo):** Wikilinks no corpo devem ter contexto textual quando possivel. Ex: "chama [[ProcessPayment]] para executar a transacao" em vez de apenas "[[ProcessPayment]]". Para knowledge-nodes com muitas relacoes, links no frontmatter (`relations`) sao aceitaveis sem contexto textual.
**Relacao com outros papeis:** Knowledge-nodes sao referenciados pelo ator pai (secao "Knowledge Nodes") e podem ser referenciados por bridge notes (topics, discussions) quando relevante. Knowledge-nodes entre si se referenciam via `relations` e edges do graph.json.

### Criterio de Completude

Um knowledge-node esta completo quando: tem `graphify_node_id` valido, `actor` definido, `node_type` definido, `source_file` identificado, e `description` auto-contida. Se faltam `graphify_node_id` ou `actor`, o conteudo deve ir para `fleeting/`.

## Exemplos

### Isso E um knowledge-node

1. "A funcao `ProcessTransaction` em `src/Controllers/PaymentController.cs` do `billing-api` e responsavel por orquestrar o fluxo de processamento com o provedor selecionado." — Funcao especifica de um ator, extraida por AST. E knowledge-node.

2. "A classe `KafkaEventPublisher` implementa o padrao de publicacao de eventos para topicos Kafka seguindo o contrato de pedidos." — Classe interna de um ator. E knowledge-node.

3. "O endpoint `POST /v1/payments/authorize` recebe requests de autorizacao e delega ao `AuthorizationService`." — Endpoint de API de um ator. E knowledge-node.

### Isso NAO e um knowledge-node

1. "O billing-api esta sendo refatorado para suportar internacionalizacao." — Informacao de alto nivel sobre o ator. E um topic.

2. "Decidimos na daily que o padrao de retry vai mudar para exponential backoff." — Decisao tomada em reuniao. E uma discussion.

3. "Talvez exista um race condition no void worker." — Hipotese sem confirmacao. E fleeting.
