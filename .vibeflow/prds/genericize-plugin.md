# PRD: Genericizar o Bedrock Plugin

> Generated via /vibeflow:discover on 2026-04-13

## Problem

O Bedrock plugin foi construido para uso interno da StoneCo. Todos os exemplos, templates, entity definitions e skills contêm referências hardcoded à Stone — emails `@stone.com.br`, repositórios `stone-payments/*`, Atlassian `allstone.atlassian.net`, subsidiárias (Stone, Pagar.me, Ton), e domínios de negócio específicos (acquiring, boleto, pix, cards).

Isso impede que qualquer pessoa fora da Stone instale o plugin e o use no vault dela. O plugin já é open-source e genérico na arquitetura, mas o conteúdo está preso a uma empresa específica.

## Target Audience

Qualquer usuário de Obsidian que queira estruturar um Second Brain com automação via Claude Code — engenheiros, PMs, CTOs, pesquisadores, independente de empresa ou domínio.

## Proposed Solution

Substituir todas as referências Stone-específicas por exemplos genéricos e neutros, mantendo a mesma estrutura e qualidade dos exemplos. Especificamente:

1. **Templates** — Trocar emails, repos, e exemplos por equivalentes genéricos (e.g. `user@company.com`, `org/my-api`)
2. **Entity definitions** — Remover menções à StoneCo e subsidiárias, usar exemplos de domínios variados
3. **Skills** — Trocar URLs de Atlassian, GitHub orgs, e exemplos de comandos por placeholders genéricos
4. **CLAUDE.md** — Remover domínios Stone da tabela de tags, manter a tabela com domínios de exemplo genéricos
5. **README.md** — Remover qualquer referência à Stone como empresa-alvo
6. **Tags `domain/*`** — Substituir domínios Stone (`acquiring`, `boleto`, `pix`, `cards`, `insurance`, `marketplace`, `orders`) por exemplos genéricos (`backend`, `frontend`, `infra`, `data`, `mobile`, `platform`, `security`)
7. **Tags `scope/*`** — Manter `pci`, `sox`, `lgpd` como exemplo de uma categoria de uso (fintech/compliance), e adicionar exemplos de outras áreas (e.g. `hipaa` para saúde, `gdpr` para empresas europeias, `soc2` para SaaS)
8. **Idioma pt-BR** — Manter como está por agora; será configurável via `/init` em trabalho futuro

## Success Criteria

- Nenhuma ocorrência de "Stone", "StoneCo", "Pagar.me", "Ton", "stone.com.br", "stone-payments", "allstone.atlassian.net" nos arquivos do plugin
- Todos os exemplos fazem sentido para um usuário que nunca ouviu falar da Stone
- O plugin continua funcional — mesma estrutura, mesmas skills, mesmos entity types
- Exemplos são variados o suficiente para demonstrar a flexibilidade do plugin (não apenas trocar Stone por outra empresa específica)

## Scope v0

- [ ] Varrer e substituir referências em `templates/` (7 arquivos)
- [ ] Varrer e substituir referências em `entities/` (9 arquivos)
- [ ] Varrer e substituir referências em `skills/` (5 arquivos)
- [ ] Atualizar tabelas de tags em `CLAUDE.md` (domínios genéricos, scope com exemplos multi-área)
- [ ] Atualizar `README.md`
- [ ] Validar que nenhuma referência Stone sobreviveu via grep

## Anti-scope

- **Não** alterar a arquitetura do plugin (entity types, skills, zettelkasten roles)
- **Não** adicionar funcionalidade de configuração/init (será feito depois)
- **Não** mudar o idioma padrão de pt-BR (será configurável via `/init`)
- **Não** alterar `plugin.json` (metadata do autor permanece)
- **Não** criar novos entity types ou skills
- **Não** alterar a lógica das skills — apenas exemplos e textos descritivos

## Technical Context

- O projeto é markdown-only — não há build, testes ou CI. A validação é textual (grep por referências remanescentes).
- Arquivos afetados estão em 4 diretórios: `templates/`, `entities/`, `skills/`, raiz (`CLAUDE.md`, `README.md`)
- Total estimado: ~24 arquivos markdown para revisar
- Wikilinks internos nos exemplos devem ser atualizados para nomes genéricos consistentes entre si (e.g. se um template menciona `[[payment-card-api]]`, trocar por `[[billing-api]]` ou similar e manter consistência em todos os arquivos)

## Open Questions

Nenhuma.
