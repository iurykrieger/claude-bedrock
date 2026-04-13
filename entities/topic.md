# Entity: Topic

> Fonte de verdade para campos obrigatórios: `topics/_template.md`

## O que é

Um **topic** é um assunto transversal com lifecycle próprio (open → in-progress → completed/cancelled). Topics representam iniciativas, incidentes, RFCs, deprecações, ou qualquer tema que evolui no tempo e afeta múltiplos atores ou pessoas. São o "tracker" de assuntos do Second Brain.

Topics têm status, histórico de eventos, decisões tomadas, e próximos passos. São o lugar onde se registra **o que está acontecendo** com um tema ao longo do tempo.

## Quando criar

- O conteúdo descreve uma iniciativa transversal que afeta mais de 1 ator (ex: migração de observabilidade, depreciação de serviços)
- O conteúdo relata um incidente ou problema sistêmico com impacto cross-team
- O conteúdo propõe uma RFC ou mudança arquitetural que precisa de tracking
- O conteúdo descreve um processo de deprecação de um sistema

## Quando NÃO criar

- É uma tarefa pontual sem evolução temporal (ex: "corrigir o bug X no PR #123") — isso é trabalho operacional, não topic
- É um bug isolado em um único ator sem impacto cross-team — registrar como known_issue no actor
- É uma feature request sem impacto transversal — pode ser um item em um project, não um topic
- É uma conversa/reunião — isso é uma discussion. Topics são assuntos; discussions são eventos

## Como distinguir de outros tipos

| Parece ser... | Mas é... | Diferença-chave |
|---|---|---|
| Topic | Discussion | Discussion é um evento pontual (reunião, conversa) com data fixa. Topic é um assunto que evolui no tempo com status e histórico |
| Topic | Project | Project tem deadline, deliverables, e focal points. Topic é mais aberto — pode não ter deadline definida. Ex: "deprecação do legacy-gateway" é topic; "migração para orders-api v2" é project |
| Topic | Actor (known_issue) | Se o problema afeta só 1 ator e é técnico, vai como known_issue no actor. Se afeta múltiplos atores ou tem impacto organizacional, é topic |

## Campos obrigatórios (frontmatter)

| Campo | Tipo | Descrição |
|---|---|---|
| `type` | string | Sempre `"topic"` |
| `title` | string | Título descritivo do assunto |
| `category` | string | `bugfix`, `troubleshooting`, `rfc`, `incident`, `feature`, `deprecation`, `compliance` |
| `status` | string | `open`, `in-progress`, `completed`, `cancelled` |
| `people` | array | Wikilinks para persons: `["[[first-last]]"]` |
| `actors` | array | Wikilinks para actors: `["[[repo-name]]"]` |
| `objective` | string | Objetivo do topic em pt-BR |
| `created_at` | date | YYYY-MM-DD |
| `updated_at` | date | YYYY-MM-DD |
| `updated_by` | string | Quem atualizou |

## Papel Zettelkasten

**Classificação:** bridge note
**Propósito no grafo:** Conectar notas permanentes (actors, people, teams) explicando *porquê* se relacionam no contexto de um assunto que evolui no tempo.

### Regras de Linking

**Links estruturais (frontmatter):** `people` (wikilinks para persons envolvidas), `actors` (wikilinks para actors afetados). Definem quais permanentes este assunto conecta.
**Links semânticos (corpo):** Links no corpo são o ponto central de um topic — devem explicar a relação entre permanentes com contexto rico. Ex: "a deprecação do [[legacy-gateway]] está bloqueada porque clientes do sistema legado ainda dependem da tokenização provida por [[billing-api]]" em vez de apenas "[[legacy-gateway]] e [[billing-api]]". O corpo do topic é onde vive a explicação da conexão entre permanentes.
**Relação com outros papéis:** Topics são o tecido conectivo entre permanentes. Se dois actors se relacionam, a explicação vive aqui — não duplicada em ambos os actors. Topics são referenciados por index notes (projects) que organizam múltiplos assuntos sob um objetivo.

### Critério de Completude

Um topic está completo quando: tem objetivo definido, pelo menos 1 actor ou person referenciado com contexto, e status atualizado. Se o assunto é vago, sem atores concretos ou objetivo claro, o conteúdo deve ir para `fleeting/` até amadurecer.

## Exemplos

### Isso É um topic

1. "Estamos migrando todos os serviços Go de dd-trace para OpenTelemetry. Afeta notification-service, crypto-service, orders-api, e metrics-collector." — Iniciativa transversal com múltiplos atores. É topic (category: `rfc`).

2. "A depreciação do legacy-gateway está bloqueada pela migração dos clientes do sistema legado. Status: em andamento desde março." — Assunto com lifecycle e status. É topic (category: `deprecation`).

### Isso NÃO é um topic

1. "Preciso corrigir o timeout no endpoint /create do notification-service." — Bug pontual em 1 ator. Vai como known_issue no actor, não como topic.

2. "Tivemos uma reunião sobre o plano de deprecação na segunda-feira." — Isso é uma discussion (evento). O plano de deprecação em si pode ser um topic.
