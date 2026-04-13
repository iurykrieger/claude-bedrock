# Entity: Fleeting

> Fonte de verdade para campos obrigatórios: `fleeting/_template.md`

## O que é

Uma **fleeting note** é uma captura de informação bruta — ideias, conceitos nascendo, menções vagas, fragmentos sem contexto completo. Fleeting notes são o inbox do vault: recebem conteúdo que ainda não atingiu o limiar de nota permanente ou bridge.

Fleeting notes são **temporárias por design**. Devem ser promovidas (→ permanent ou bridge) ou arquivadas dentro de um período razoável. Não são lixo — são informação em maturação.

## Papel Zettelkasten

**Classificação:** fleeting note
**Propósito no grafo:** Capturar informação em formação que ainda não é consolidada o suficiente para ser uma nota permanente ou bridge.

### Regras de Linking

**Links estruturais (frontmatter):** `source` (wikilink para a source de onde veio, ou `"session"` se capturada diretamente), `promoted_to` (wikilink para nota destino quando promovida).
**Links semânticos (corpo):** Links no corpo são exploratórios — podem referenciar permanentes ou bridges existentes que parecem relacionados, mas sem a obrigação de contexto textual completo. Fleeting notes são rascunhos; a exigência de linking semântico se aplica quando promovidas.
**Relação com outros papéis:** Fleeting notes referenciam permanentes e bridges existentes como "pistas" de conexão. Quando promovidas, o conteúdo migra para uma permanent (actor, person, team) ou bridge (topic, discussion) seguindo as regras de linking daquele tipo.

### Critério de Completude

Fleeting notes **não precisam** estar completas — esse é o ponto. Elas existem justamente para capturar informação incompleta. O critério relevante é o de **promoção** (ver abaixo).

## Quando criar

- O conteúdo ingerido pelo `/teach` contém ideias, menções ou fragmentos que não atendem os critérios de completude de nenhum tipo permanente ou bridge
- O conteúdo menciona algo potencialmente útil mas sem dados suficientes para criar uma entidade (ex: "alguém mencionou um novo serviço de tokenização" — sem nome, repo, ou time)
- O conteúdo captura uma hipótese, sugestão, ou rascunho de ideia que precisa ser lapidado
- O `/preserve` recebe conteúdo que não passa nos critérios de completude de nenhum tipo

## Quando NÃO criar

- O conteúdo já tem dados suficientes para criar uma entidade permanente ou bridge — criar diretamente no tipo correto
- O conteúdo é irrelevante para o vault (ruído, conversa casual, informação off-topic)
- O conteúdo é uma duplicata de algo já capturado em outra fleeting note ou entidade existente

## Como distinguir de outros tipos

| Parece ser... | Mas é... | Diferença-chave |
|---|---|---|
| Fleeting | Actor | Se tem repo, deploy, e time — é actor. Se só "alguém mencionou um serviço novo" sem detalhes, é fleeting |
| Fleeting | Person | Se tem nome completo e time — é person. Se só "um engenheiro do payments", é fleeting |
| Fleeting | Topic | Se tem objetivo claro e actors afetados — é topic. Se é "talvez a gente precise deprecar X", é fleeting |
| Fleeting | Discussion | Se tem data, participantes, e decisões — é discussion. Se é "parece que houve uma reunião sobre Y", é fleeting |

## Critérios de Promoção

Uma fleeting note deve ser promovida a permanent ou bridge quando **qualquer** dos 3 critérios for atendido:

### 1. Massa crítica

A fleeting note acumula informação suficiente para ser auto-contida:
- Mais de 3 parágrafos com fontes verificáveis
- Dados concretos (nomes, datas, números, repositórios)
- Contexto suficiente para atender os critérios de completude do tipo destino

### 2. Corroboração

A informação da fleeting note é confirmada ou complementada por uma nota permanente existente:
- Uma nova ingestão via `/teach` traz dados que validam ou expandem a fleeting
- Uma permanent existente é atualizada com informação que confirma o conteúdo da fleeting
- Duas ou mais fleeting notes sobre o mesmo assunto são consolidáveis numa nota permanente

### 3. Relevância ativa

O `/bedrock` referencia a fleeting note em resposta a uma query, sinalizando que a informação é útil:
- O conteúdo da fleeting é citado como resposta a uma pergunta do usuário
- A fleeting contribui para o entendimento de um assunto ativo no vault
- Neste caso, o `/bedrock` sinaliza a oportunidade de promoção

## Pipeline de promoção

1. **Detecção** — `/preserve`, `/teach`, ou `/bedrock` identifica que um critério de promoção foi atingido
2. **Sinalização** — O skill sinaliza com callout: `> [!info] Promoção sugerida: esta nota pode ser promovida a <tipo>`
3. **Promoção** — O `/preserve` é invocado para criar a entidade destino, migrando o conteúdo relevante
4. **Atualização** — A fleeting note recebe `status: promoted` e `promoted_to: [[nota-destino]]`

## Campos obrigatórios (frontmatter)

| Campo | Tipo | Descrição |
|---|---|---|
| `type` | string | Sempre `"fleeting"` |
| `title` | string | Título descritivo curto |
| `source` | wikilink/string | `"[[source-name]]"` ou `"session"` |
| `captured_at` | date | YYYY-MM-DD da captura |
| `status` | string | `raw`, `reviewing`, `promoted`, `archived` |
| `promoted_to` | wikilink/string | `"[[nota-destino]]"` ou `""` (vazio até promoção) |
| `updated_at` | date | YYYY-MM-DD |
| `updated_by` | string | Quem atualizou |

## Status possíveis

| Status | Descrição |
|---|---|
| `raw` | Recém-capturada, sem revisão |
| `reviewing` | Em análise — alguém ou algum skill está avaliando para promoção |
| `promoted` | Promovida — conteúdo migrou para nota permanente/bridge (ver `promoted_to`) |
| `archived` | Arquivada — conteúdo não era relevante ou ficou obsoleto |

## Exemplos

### Isso É uma fleeting note

1. "Alguém mencionou um novo serviço de tokenização que vai substituir o legacy-gateway, mas não sei o nome nem o repo." — Informação útil mas incompleta. É fleeting até ter dados concretos.

2. "Parece que o squad Notifications está pensando em migrar o crypto-service para Rust. Precisa confirmar." — Hipótese sem confirmação. É fleeting até ser validada.

3. "Em alguma reunião falaram sobre mudar o provedor de SMS para notificações. Não sei quando nem quem estava." — Fragmento sem data, participantes, ou decisão. É fleeting.

### Isso NÃO é uma fleeting note

1. "O health-checker é um serviço Go que substitui o MonitorAPI. Repo: acme-corp/health-checker. Squad Orders é responsável." — Dados concretos suficientes para ser actor.

2. "Reunião de planning (01/04/2026): Alice, Bob, Carol. Decisão: priorizar migração legacy-gateway." — Dados completos para ser discussion.
