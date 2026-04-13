# Campo: sources (proveniencia)

> Documentacao do campo `sources` no frontmatter das entidades.

## O que e

O campo `sources` e um array no frontmatter de qualquer entidade que registra de onde vieram as informacoes — uma pagina do Confluence, um Google Doc, um CSV, um repositorio GitHub. NAO e um tipo de entidade; e metadata de rastreabilidade embutida na propria entidade.

O campo permite re-ingestao: ao registrar a URL/path e a data da ultima sincronizacao, o `/sync` sabe quais fontes estao desatualizadas e podem ser reconsultadas.

## Schema

```yaml
sources:
  - url: "https://mycompany.atlassian.net/wiki/spaces/PROC/pages/..."
    type: "confluence"
    synced_at: 2026-04-09
  - url: "https://github.com/acme-corp/billing-api"
    type: "github-repo"
    synced_at: 2026-04-10
```

| Campo | Tipo | Obrigatorio | Descricao |
|---|---|---|---|
| `url` | string | sim | URL ou path local da fonte |
| `type` | string | sim | `confluence`, `gdoc`, `github-repo`, `csv`, `markdown`, `manual` |
| `synced_at` | date | sim | YYYY-MM-DD da ultima sincronizacao |

## Regras de merge

- **Append-only:** novas sources sao adicionadas, nunca removidas
- **Dedup por URL:** se a URL ja existe na lista, atualizar `synced_at` (nao duplicar a entry)
- **Ordem:** mais recente primeiro (por `synced_at`)

## Quando popular

- Uma fonte externa foi ingerida via `/teach` e o conteudo gerou ou atualizou esta entidade
- O `/sync` re-sincronizou uma fonte e atualizou `synced_at`
- O usuario quer registrar manualmente a proveniencia de uma entidade

## Quando NAO popular

- O conteudo foi digitado diretamente pelo usuario sem referencia a documento externo — nao ha fonte para registrar
- A fonte e a memoria da sessao do agente — isso e implicito, nao precisa de registro
- A fonte e um commit ou PR do GitHub — isso ja e rastreado pelo git history

## Como o /sync usa o campo

1. Varre todas as entidades do vault extraindo o campo `sources`
2. Deduplica por URL (uma URL pode aparecer em multiplas entidades)
3. Para cada URL unica com tipo sincronizavel (`confluence`, `gdoc`, `github-repo`, `markdown`):
   - Re-busca o conteudo atualizado
   - Compara com entidades existentes (diff incremental)
   - Atualiza `synced_at` em todas as entidades que referenciam aquela URL

## Relacao com campo `source` (singular)

Discussions e fleeting notes possuem um campo `source` (string singular) que indica o contexto de captura: `session`, `meeting-notes`, `teach`, `manual`. Este campo tem semantica diferente:

| Campo | Tipo | Semantica | Exemplo |
|---|---|---|---|
| `source` (singular) | string | Como a entidade foi capturada | `"meeting-notes"` |
| `sources` (plural) | array | De onde vieram os dados externos | `[{url: "...", type: "confluence", synced_at: "..."}]` |

Ambos podem coexistir na mesma entidade. Sao independentes.

## Exemplos

### Entidade com source unica

```yaml
sources:
  - url: "https://mycompany.atlassian.net/wiki/spaces/PROC/pages/8675099062"
    type: "confluence"
    synced_at: 2026-04-09
```

### Entidade com multiplas sources

```yaml
sources:
  - url: "https://github.com/acme-corp/billing-api"
    type: "github-repo"
    synced_at: 2026-04-10
  - url: "https://mycompany.atlassian.net/wiki/spaces/PROC/pages/123"
    type: "confluence"
    synced_at: 2026-04-05
```

### Entidade sem source externa

```yaml
sources: []
```
