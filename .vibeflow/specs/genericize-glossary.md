# Glossário de Substituições: Stone → Genérico

> Referência canônica para as parts 1, 2 e 3 da genericização do Bedrock plugin.
> Criado em 2026-04-13.

## Sistemas (actors)

| Stone (original) | Genérico (novo) | Descrição |
|---|---|---|
| `payment-card-api` | `billing-api` | API de cobrança |
| `boleto-api` | `notification-service` | Serviço de notificações |
| `autobahn` | `legacy-gateway` | Gateway legado em deprecação |
| `charge-probe` | `health-checker` | Probe de saúde |
| `decryptor` | `crypto-service` | Serviço de criptografia |
| `pix-receiver` | `webhook-receiver` | Receptor de webhooks |
| `brand-retry-blocker` | `rate-limiter` | Limitador de taxa |
| `boleto-recovery-consumer` | `retry-consumer` | Consumer de retry |
| `charge-api` | `orders-api` | API de pedidos |
| `probe-consumer` | `metrics-collector` | Coletor de métricas |
| `ProbeAPI` | `MonitorAPI` | API de monitoramento legada |
| `charge-cdc` | `orders-cdc` | CDC do workspace orders |
| `payment-new-api` | `billing-new-api` | Nova API de cobrança |

## Pessoas

| Stone (original) | Genérico (novo) | Notas |
|---|---|---|
| `Iury Krieger` / `iury.krieger` / `iury-krieger` | `Alice Smith` / `alice.smith` / `alice-smith` | Placeholder principal |
| `Leonardo Bittencourt` / `leonardo-otero` / `Leonardo` | `Bob Jones` / `bob-jones` / `Bob` | Segundo placeholder |
| `Giovanna` | `Carol` | Terceiro placeholder |
| `Jaderson Gomes` / `jadersgomes` | `Dave Wilson` / `davewilson` | Quarto placeholder |
| `Maria Silva` | `Eve Martin` | Quinto placeholder |
| `Fulano` | `Alice` | Placeholder genérico pt-BR → inglês |
| `Ciclano` | `Bob` | Placeholder genérico pt-BR → inglês |
| `Beltrano` | `Carol` | Placeholder genérico pt-BR → inglês |

## Squads/Times

| Stone (original) | Genérico (novo) |
|---|---|
| `Squad Acquiring` / `squad-acquiring` | `Squad Payments` / `squad-payments` |
| `Squad Boleto` / `squad-boleto` | `Squad Notifications` / `squad-notifications` |
| `Squad Charge` / `squad-charge` | `Squad Orders` / `squad-orders` |

## Domínios (tags)

| Stone (original) | Genérico (novo) |
|---|---|
| `acquiring` | `payments` |
| `boleto` | `notifications` |
| `cards` | `checkout` |
| `charge` | `orders` |
| `pix` | `integrations` |
| `banking` | `finance` |
| `insurance` | `compliance` |
| `staffs` | `internal-tools` |
| `marketplace` | `marketplace` (sem mudança) |
| `orders` | `orders` (sem mudança) |
| `core` | `core` (sem mudança) |
| `data` | `data` (sem mudança) |
| `infra` | `infra` (sem mudança) |
| `platform` | `platform` (sem mudança) |
| `security` | `security` (sem mudança) |

## URLs e Organizações

| Stone (original) | Genérico (novo) |
|---|---|
| `stone-payments` | `acme-corp` |
| `allstone.atlassian.net` | `mycompany.atlassian.net` |
| `stone.com.br` | `company.com` |
| `@stone.com.br` | `@company.com` |
| `iury.krieger@stone.com.br` | `alice.smith@company.com` |

## Empresa/Subsidiárias

| Stone (original) | Genérico (novo) |
|---|---|
| `StoneCo` | Remover — substituir por "da organização" ou "da empresa" conforme contexto |
| `Stone` (como empresa) | Remover — substituir por "da organização" ou "da empresa" |
| `Pagar.me` | Remover — `clientes Pagar.me` → `clientes do sistema legado` |
| `Ton` | Remover completamente |

## Outros

| Stone (original) | Genérico (novo) |
|---|---|
| `SafraPay` | `PartnerPay` |
| `runtime-acquiring-prd` | `runtime-payments-prd` |
| `OneV2 Charge API` | `V2 Orders API` |
| `#acquiring-alerts` | `#payments-alerts` |
| `card engine` | `billing engine` |
| `pix engine` | `integration engine` |
| `2026-06-deprecation-autobahn` | `2026-06-deprecation-legacy-gateway` |
| `PCA` (alias) | `BillingAPI` (alias) |
