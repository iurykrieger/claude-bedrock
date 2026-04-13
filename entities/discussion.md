# Entity: Discussion

> Fonte de verdade para campos obrigatórios: `discussions/_template.md`

## O que é

Uma **discussion** é o registro de uma conversa, reunião, ou troca de ideias que aconteceu em um momento específico. Discussions capturam: quem participou, o que foi discutido, quais decisões foram tomadas, e quais ações ficaram pendentes.

Discussions são **eventos pontuais com data fixa** — não evoluem no tempo como topics. Após criadas, são apenas atualizadas para refletir o progresso dos action items, nunca para adicionar novos tópicos à mesma discussion.

## Quando criar

- O conteúdo é uma ata de reunião ou meeting notes com participantes e decisões
- O conteúdo registra uma conversa que gerou decisões ou action items relevantes para o vault
- O conteúdo descreve um alinhamento/planning com múltiplas pessoas e impacto em atores

## Quando NÃO criar

- É documentação técnica, spec, ou PRD — isso são documentos de referência, não discussions
- É um changelog ou release notes — isso é atividade de um actor
- É uma thread do Slack com informação pontual sem decisões — só vale se teve decisão ou action item
- É uma conversa 1:1 casual sem impacto no vault — discussions registram eventos relevantes

## Como distinguir de outros tipos

| Parece ser... | Mas é... | Diferença-chave |
|---|---|---|
| Discussion | Topic | Topic é um assunto que evolui (status, histórico). Discussion é um evento com data fixa. Uma reunião sobre deprecação é discussion; a deprecação em si é topic |
| Discussion | Project | Project tem deliverables e deadline. Discussion é registro de uma conversa. Uma reunião de planning pode gerar uma discussion E resultar na criação de um project |
| Discussion | Source | Se o conteúdo é meeting notes sendo ingeridas, a fonte é source. O conteúdo extraído da fonte pode gerar uma discussion |

## Campos obrigatórios (frontmatter)

| Campo | Tipo | Descrição |
|---|---|---|
| `type` | string | Sempre `"discussion"` |
| `title` | string | Título descritivo da conversa |
| `date` | date | YYYY-MM-DD da conversa |
| `summary` | string | Resumo em 1-2 frases |
| `conclusions` | array | Lista de decisões tomadas |
| `action_items` | array | Lista de ações pendentes |
| `related_topics` | array | Wikilinks para topics |
| `related_actors` | array | Wikilinks para actors |
| `related_people` | array | Wikilinks para persons |
| `related_projects` | array | Wikilinks para projects |
| `related_teams` | array | Wikilinks para teams |
| `source` | string | `session`, `meeting-notes`, `jira`, `confluence`, `manual` |
| `updated_at` | date | YYYY-MM-DD |
| `updated_by` | string | Quem atualizou |

## Papel Zettelkasten

**Classificação:** bridge note
**Propósito no grafo:** Registrar o momento em que permanentes (people, actors, teams) se conectaram através de uma conversa, decisão, ou troca de ideias.

### Regras de Linking

**Links estruturais (frontmatter):** `related_people`, `related_actors`, `related_teams`, `related_topics`, `related_projects` (wikilinks). Definem quais entidades participaram ou foram discutidas no evento.
**Links semânticos (corpo):** Links no corpo devem contextualizar a participação ou menção. Ex: "[[bob-jones]] apresentou a proposta de migração do [[legacy-gateway]] para o [[billing-api]]" em vez de apenas listar nomes. O corpo da discussion é a narrativa do evento — quem disse o quê sobre qual sistema e por qual razão.
**Relação com outros papéis:** Discussions são pontes temporais — registram quando e como permanentes se conectaram num momento específico. Diferem de topics porque são eventos pontuais, não assuntos que evoluem. Uma discussion pode gerar ou atualizar topics e projects.

### Critério de Completude

Uma discussion está completa quando: tem data, pelo menos 1 participante (person), resumo do que foi discutido, e pelo menos 1 conclusão ou action item. Se só há menção de "uma reunião aconteceu" sem detalhes, o conteúdo deve ir para `fleeting/` até ser enriquecido.

## Exemplos

### Isso É uma discussion

1. "Reunião de planning Q2 (01/04/2026): participaram Alice, Bob, Carol. Decisão: priorizar migração do legacy-gateway. Action: Bob vai mapear dependências até sexta." — Meeting notes com participantes, decisão, e action item. É discussion.

2. "Alinhamento sobre observabilidade (03/04/2026): decidimos migrar de DataDog para OpenTelemetry nos serviços Go. Responsável: squad Notifications começa pelo crypto-service." — Conversa com decisão e ação. É discussion.

### Isso NÃO é uma discussion

1. "Documento de arquitetura do orders-api descrevendo o fluxo hexagonal." — Documentação técnica. Não é discussion.

2. "Release notes v2.3.0 do billing-api: adicionado suporte a PartnerPay." — Changelog de um actor. Não é discussion.
