# Entity: Project

> Fonte de verdade para campos obrigatórios: `projects/_template.md`

## O que é

Um **project** é uma iniciativa com escopo fechado, deadline (real ou estimada), deliverables concretos, e focal points responsáveis. Projects agregam múltiplos atores, pessoas, e topics sob um objetivo comum. São o "hub" de uma iniciativa no Second Brain.

Projects têm status (planning → active → blocked → completed), progresso rastreável, e bloqueios explícitos. Diferem de topics por serem mais concretos e orientados a entrega.

## Quando criar

- O conteúdo descreve uma iniciativa com objetivo, escopo, e pelo menos 1 responsável (focal point)
- O conteúdo menciona uma migração, rewrite, ou construção de sistema novo com timeline
- O conteúdo define deliverables e marcos de um esforço cross-team

## Quando NÃO criar

- É um assunto/tema sem deadline ou deliverables concretos — isso é um topic
- É uma conversa/reunião — isso é uma discussion (que pode referenciar um project)
- É uma tarefa isolada de 1 pessoa em 1 ator — isso é trabalho operacional, não project
- É a operação contínua de um sistema — isso é o próprio actor

## Como distinguir de outros tipos

| Parece ser... | Mas é... | Diferença-chave |
|---|---|---|
| Project | Topic | Topic é um assunto aberto (ex: "deprecação de serviços legados"). Project é uma iniciativa fechada (ex: "migrar legacy-gateway para billing-api até Q3"). Topic pode existir sem deadline; project sempre tem (mesmo que estimada) |
| Project | Actor | Se o resultado final é um sistema novo, ele começa como project e vira actor quando tiver repo e deploy. Ex: "projeto de criação do health-checker" → depois vira actor `health-checker` |
| Project | Discussion | Discussion é evento pontual. Project é esforço contínuo com progresso. Uma discussion pode criar ou atualizar um project |

## Campos obrigatórios (frontmatter)

| Campo | Tipo | Descrição |
|---|---|---|
| `type` | string | Sempre `"project"` |
| `name` | string | Nome do projeto |
| `description` | string | Descrição em pt-BR |
| `status` | string | `planning`, `active`, `blocked`, `completed` |
| `deadline` | string | Data limite ou vazio |
| `progress` | string | Descrição do progresso atual |
| `blockers` | array | Lista de bloqueios |
| `focal_points` | array | Wikilinks para persons: `["[[first-last]]"]` |
| `related_topics` | array | Wikilinks para topics |
| `related_actors` | array | Wikilinks para actors |
| `related_teams` | array | Wikilinks para teams |
| `updated_at` | date | YYYY-MM-DD |
| `updated_by` | string | Quem atualizou |

## Papel Zettelkasten

**Classificação:** index note
**Propósito no grafo:** Organizar caminhos de leitura — agregar bridges (topics, discussions) e permanentes (actors, people, teams) sob um objetivo comum, funcionando como Map of Content (MOC) temático.

### Regras de Linking

**Links estruturais (frontmatter):** `focal_points` (wikilinks para persons), `related_topics`, `related_actors`, `related_teams` (wikilinks). Definem quais entidades compõem esta iniciativa.
**Links semânticos (corpo):** Links no corpo devem apontar para onde o conhecimento está, sem repetir conteúdo. Ex: "o progresso da migração está documentado em [[2026-06-deprecation-legacy-gateway]]" em vez de replicar o histórico aqui. O corpo do project é curadoria — direciona o leitor para as notas certas.
**Relação com outros papéis:** Projects não contêm conhecimento próprio — apontam para bridges (topics que detalham os assuntos) e permanentes (actors e people envolvidos). Se um project está explicando algo em detalhe, esse detalhe deveria estar num topic.

### Critério de Completude

Um project está completo quando: tem objetivo, pelo menos 1 focal point, e referências para topics ou actors relacionados. Se é apenas uma ideia de iniciativa sem responsável ou escopo concreto, o conteúdo deve ir para `fleeting/` até ser definido.

## Exemplos

### Isso É um project

1. "Migração do legacy-gateway para billing-api: deadline Q3/2026. Responsável: Bob. Bloqueio: clientes do sistema legado que ainda usam o legacy-gateway." — Iniciativa com deadline, responsável, bloqueio. É project.

2. "V2 Orders API: estamos construindo a nova API de pedidos. Squad Orders lidera, previsão de go-live em maio. Envolve orders-api, billing engine, integration engine." — Esforço de construção com timeline e múltiplos atores. É project.

### Isso NÃO é um project

1. "A gente precisa melhorar a observabilidade dos serviços Go." — Assunto aberto sem deadline nem deliverable concreto. É topic.

2. "Corrigir o bug de timeout no notification-service até sexta." — Tarefa pontual de 1 pessoa. Não é project.
