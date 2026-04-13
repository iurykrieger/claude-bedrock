# Entity: Actor

> Fonte de verdade para campos obrigatórios: `actors/_template.md`

## O que é

Um **actor** é um sistema, serviço, API ou aplicação com ciclo de vida próprio — possui repositório no GitHub, processo de deploy independente, e é operado por um time específico. Actors são a unidade fundamental de infraestrutura no Second Brain: cada ator representa algo que roda em produção (ou já rodou, se deprecated).

Actors podem ser APIs HTTP, workers/consumers de fila, cronjobs, lambdas, ou monolitos. O critério-chave é: **tem repositório próprio e deploy independente**.

## Quando criar

- O conteúdo menciona um sistema/serviço com repositório GitHub próprio que ainda não existe em `actors/`
- O conteúdo descreve uma nova aplicação sendo desenvolvida (status: `in-development`)
- O conteúdo referencia um repositório da organização GitHub da empresa não catalogado

## Quando NÃO criar

- É uma biblioteca/SDK interna usada por outros atores (ex: `opentelemetry-golang-lib`) — isso é uma dependência, não um ator
- É um módulo dentro de outro repositório (ex: `orders-cdc` dentro do workspace `orders-api`) — o ator é o repositório raiz
- É uma ferramenta de CI/CD ou infraestrutura compartilhada (ex: ArgoCD, Karavela, Terraform modules)
- É um serviço externo/third-party (ex: DataDog, New Relic, AWS SQS) — mencione como dependência de um ator, não como ator próprio

## Como distinguir de outros tipos

| Parece ser... | Mas é... | Diferença-chave |
|---|---|---|
| Actor | Topic (deprecation) | Se o foco é "este sistema vai ser desligado", é um topic de deprecação que **referencia** o actor. O actor é o sistema; o topic é o assunto sobre ele |
| Actor | Project | Se o foco é "estamos construindo um sistema novo", é um project até o sistema ter repo e deploy. Depois de criado, o sistema vira actor |
| Actor | Person | Nomes de repo podem parecer nomes de pessoas (ex: `ralph`). Se tem repo GitHub e faz deploy, é actor |

## Campos obrigatórios (frontmatter)

| Campo | Tipo | Descrição |
|---|---|---|
| `type` | string | Sempre `"actor"` |
| `name` | string | Nome do repositório (kebab-case) |
| `category` | string | `api`, `worker`, `consumer`, `producer`, `cronjob`, `lambda`, `monolith` |
| `description` | string | Descrição em pt-BR da função do sistema |
| `repository` | string | URL do repositório GitHub |
| `stack` | string | Stack técnica separada por ` · ` |
| `status` | string | `active`, `deprecated`, `in-development` |
| `team` | wikilink | `"[[squad-name]]"` |
| `criticality` | string | `very-high`, `high`, `medium`, `low` |
| `pci` | boolean | Se opera em escopo PCI DSS |
| `updated_at` | date | YYYY-MM-DD |
| `updated_by` | string | Quem atualizou |

## Papel Zettelkasten

**Classificação:** permanent note
**Propósito no grafo:** Representar fatos consolidados sobre sistemas e serviços que rodam em produção.

### Regras de Linking

**Links estruturais (frontmatter):** `team` (wikilink para squad responsável). Definem a estrutura organizacional — quem opera o sistema.
**Links semânticos (corpo):** Wikilinks no corpo devem ter contexto textual explicando a relação. Ex: "recebe autorizações do [[payment-gateway]] via gRPC" em vez de apenas "[[payment-gateway]]". Links no corpo explicam dependências técnicas, fluxos de dados, e integrações — o *porquê* da conexão.
**Relação com outros papéis:** Actors são referenciados por bridge notes (topics, discussions) que explicam o que está acontecendo com o sistema. Não duplicar no actor explicações que pertencem a um topic — o actor descreve o sistema, o topic descreve o assunto sobre ele.

### Critério de Completude

Um actor está completo quando: tem repositório identificado, stack documentada, status definido, time responsável atribuído, e descrição auto-contida (compreensível sem precisar ler outras notas). Se faltam dados fundamentais (sem repo, sem time, sem descrição), o conteúdo deve ir para `fleeting/` até ser consolidado.

## Exemplos

### Isso É um actor

1. "O `billing-api` é uma API .NET 8 que processa cobranças e faturas. Roda em EKS via ArgoCD no namespace `runtime-payments-prd`." — Sistema com repo, deploy, runtime. É actor.

2. "Estamos subindo o `health-checker` em Go para substituir o probe antigo. Já tem repo no GitHub e pipeline de CI." — Sistema novo com repo próprio. É actor (status: `in-development`).

### Isso NÃO é um actor

1. "Usamos a lib `opentelemetry-golang-lib` para instrumentação." — Biblioteca compartilhada, não tem deploy próprio. É dependência de actors.

2. "O ArgoCD faz o deploy de todos os serviços do squad." — Ferramenta de infra compartilhada, não tem deploy independente como produto. Não é ator.
