# Entity: Team

> Fonte de verdade para campos obrigatórios: `teams/_template.md`

## O que é

Um **team** é um squad com escopo organizacional definido, membros identificáveis, e ownership sobre um conjunto de atores. Teams são a unidade organizacional do Second Brain — representam a estrutura real de squads da organização.

Times possuem escopo de domínio (ex: "ciclo de vida de transações de cartão"), membros listados, e um conjunto de atores sob sua responsabilidade.

## Quando criar

- O conteúdo referencia um squad/time com nome formal e pelo menos 1 membro ou 1 ator sob ownership identificável
- O conteúdo descreve a criação de um novo squad com escopo definido
- O conteúdo lista membros e responsabilidades de um time não catalogado

## Quando NÃO criar

- É um grupo ad-hoc montado para um projeto específico (ex: "task force de migração") — isso é um project com focal_points, não um team
- É uma referência a um canal do Slack ou grupo de comunicação (ex: "#payments-alerts")
- É uma menção genérica ("o pessoal do backend", "a galera de infra") — sem escopo formal, não é team
- É uma referência a um time não-técnico sem ownership de sistemas (ex: "time de compliance jurídica", "time de RH") — o vault cobre times de tecnologia

## Como distinguir de outros tipos

| Parece ser... | Mas é... | Diferença-chave |
|---|---|---|
| Team | Project | Se é um grupo temporário com deadline e deliverables, é project. Team é permanente com ownership contínuo |
| Team | Person (plural) | Se o conteúdo diz "Carol e Bob do payments", são persons referenciando o team. O team já existe |
| Team | Actor | Se o conteúdo diz "o payments", pode ser o team (squad-payments) ou um actor específico. Contexto define: se fala de pessoas/ownership → team; se fala de deploy/código → actor |

## Campos obrigatórios (frontmatter)

| Campo | Tipo | Descrição |
|---|---|---|
| `type` | string | Sempre `"team"` |
| `name` | string | Nome do squad (ex: "Squad Payments") |
| `scope` | string | Escopo de atuação em pt-BR |
| `purpose` | string | Propósito/missão do time |
| `members` | array | Wikilinks para persons: `["[[first-last]]"]` |
| `actors` | array | Wikilinks para actors: `["[[repo-name]]"]` |
| `updated_at` | date | YYYY-MM-DD |
| `updated_by` | string | Quem atualizou |

## Papel Zettelkasten

**Classificação:** permanent note
**Propósito no grafo:** Representar fatos consolidados sobre squads — escopo organizacional, membros, e ownership de sistemas.

### Regras de Linking

**Links estruturais (frontmatter):** `members` (wikilinks para persons), `actors` (wikilinks para actors). Definem a composição do time — quem trabalha e quais sistemas opera.
**Links semânticos (corpo):** Wikilinks no corpo devem ter contexto textual. Ex: "responsável pela operação e evolução do [[billing-api]] e do [[rate-limiter]]" em vez de listar links soltos. Links no corpo explicam a relação do time com seus sistemas e com outros times.
**Relação com outros papéis:** Teams são referenciados por bridge notes (topics, discussions) e index notes (projects). Não duplicar no team o histórico de projetos — o team descreve a estrutura organizacional, o project descreve a iniciativa.

### Critério de Completude

Um team está completo quando: tem nome formal, escopo definido, pelo menos 1 membro listado, e pelo menos 1 actor sob ownership. Se apenas o nome do squad é mencionado sem membros ou atores, o conteúdo deve ir para `fleeting/` até ser consolidado.

## Exemplos

### Isso É um team

1. "O Squad Notifications é responsável por notification-service, retry-consumer e crypto-service. Tem 5 engenheiros." — Squad formal com atores e membros. É team.

2. "Estamos criando o Squad Orders para cuidar do ciclo de vida de pedidos. Bob vai liderar." — Novo squad com escopo definido. É team.

### Isso NÃO é um team

1. "Montamos um grupo com gente de payments e notifications para resolver o incidente." — Grupo ad-hoc/temporário. Pode ser uma discussion ou topic, não team.

2. "O time de RH ajustou o benefício de vale-refeição." — Time não-técnico sem ownership de sistemas. Fora do escopo do vault.
