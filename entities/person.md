# Entity: Person

> Fonte de verdade para campos obrigatórios: `people/_template.md`

## O que é

Uma **person** é qualquer colaborador interno da organização que seja identificável e relevante para o contexto do vault — engenheiro, tech lead, gerente, product manager, engineering manager, designer, DRI, ou qualquer outro profissional que participe de decisões, operações ou contribuições técnicas.

A identificação primária é o **prefixo do email corporativo** (ex: `alice.smith@company.com` → filename `alice-smith.md`), que garante idempotência e universalidade — todo colaborador possui email corporativo, independente de ter ou não conta no GitHub.

Persons são conectadas a teams e actors via wikilinks. O vault rastreia pessoas para entender: quem trabalha em quê, quem é focal point de qual sistema, quem participou de quais decisões, e qual é o papel de cada pessoa na organização.

## Quando criar

- O conteúdo menciona uma pessoa por nome completo E é possível associá-la a um time ou ator do vault
- O conteúdo identifica um contribuidor ativo (commits, PRs, code reviews) em repositórios de atores conhecidos
- O conteúdo nomeia um DRI, focal point, ou responsável por uma ação/decisão
- O conteúdo menciona um profissional (PM, EM, designer, etc.) que participa ativamente de um time ou projeto do vault, mesmo sem contribuição direta em código

## Quando NÃO criar

- É uma menção genérica sem nome completo (ex: "o pessoal do time de notificações", "alguém do infra") — isso é referência a team, não a person
- É um usuário final ou cliente (ex: "o lojista reportou um bug") — persons são colaboradores internos
- É um stakeholder externo sem participação direta na organização (ex: "o auditor da PCI")
- É uma pessoa mencionada apenas uma vez sem contexto de time/ator — provavelmente não é relevante para o vault

## Como distinguir de outros tipos

| Parece ser... | Mas é... | Diferença-chave |
|---|---|---|
| Person | Team | Se o conteúdo diz "a galera do payments", é referência ao team. Person é um indivíduo com nome |
| Person | Actor | Nomes como `ralph` podem ser tanto pessoa quanto repo. Se tem email corporativo e participa de um time, é person. Se tem deploy, é actor |
| Person | Discussion participant | Se a pessoa só aparece como participante de uma reunião, ela pode ser criada como person E referenciada na discussion |

## Campos obrigatórios (frontmatter)

| Campo | Tipo | Descrição |
|---|---|---|
| `type` | string | Sempre `"person"` |
| `name` | string | Nome completo da pessoa |
| `role` | string | Cargo/função em pt-BR |
| `team` | wikilink | `"[[squad-name]]"` |
| `focal_points` | array | Wikilinks para actors: `["[[repo-name]]"]` |
| `updated_at` | date | YYYY-MM-DD |
| `updated_by` | string | Quem atualizou |

## Campos opcionais (frontmatter)

| Campo | Tipo | Descrição |
|---|---|---|
| `email` | string | Email corporativo completo (ex: `alice.smith@company.com`) |
| `github` | string | Login do GitHub (quando aplicável) |
| `slack` | string | Arroba do Slack (ex: `@alice.smith`) |
| `jira` | string | Usuário do Jira |

## Convenção de filename

O filename de uma person é derivado do **prefixo do email corporativo**, normalizado:
- Pontos viram hífens: `alice.smith` → `alice-smith`
- Lowercase, sem acentos
- Exemplo: `alice.smith@company.com` → `alice-smith.md`

Quando o email não é conhecido, usar `first-last.md` baseado no nome completo (normalizado).

## Papel Zettelkasten

**Classificação:** permanent note
**Propósito no grafo:** Representar fatos consolidados sobre colaboradores internos — quem são, onde trabalham, e com quais sistemas contribuem.

### Regras de Linking

**Links estruturais (frontmatter):** `team` (wikilink para squad), `focal_points` (wikilinks para actors). Definem a posição organizacional — em qual time e em quais sistemas a pessoa atua.
**Links semânticos (corpo):** Wikilinks no corpo devem ter contexto textual. Ex: "lidera a migração do [[legacy-gateway]] para [[billing-api]]" em vez de apenas "[[legacy-gateway]]". Links no corpo explicam contribuições, responsabilidades, e envolvimento em decisões.
**Relação com outros papéis:** Persons são referenciadas por bridge notes (topics, discussions) que registram participação em eventos e assuntos. Não duplicar na person o histórico de discussions — a person descreve quem é, o topic/discussion descreve o que aconteceu.

### Critério de Completude

Uma person está completa quando: tem nome completo, time atribuído, e pelo menos 1 focal point ou papel definido. Se apenas o nome é mencionado sem contexto de time ou papel, o conteúdo deve ir para `fleeting/` até ser consolidado.

## Exemplos

### Isso É uma person

1. "Bob Jones é engenheiro do squad Payments e trabalha principalmente no billing-api." — Indivíduo com nome, time, e ator focal. É person.

2. "O PR #142 no notification-service foi aberto por `davewilson` (Dave Wilson)." — Contribuidor identificável com GitHub login e ator. É person.

3. "Eve Martin é Product Manager do squad Orders e lidera o projeto de migração V2." — Profissional com nome, time e projeto. É person, mesmo sem commits.

### Isso NÃO é uma person

1. "O time de notificações vai cuidar da migração." — Referência ao team, não a um indivíduo. Não criar person.

2. "Um lojista reportou timeout nas cobranças de cartão." — Usuário final, não contribuidor interno. Não criar person.
