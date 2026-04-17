export interface VaultFolder {
  name: string;
  icon: string;
  files: string[];
}

export const vaultFolders: VaultFolder[] = [
  { name: "actors", icon: "\uD83D\uDCE6", files: ["billing-api.md", "notification-service.md", "auth-gateway.md"] },
  { name: "people", icon: "\uD83D\uDC64", files: ["alice-smith.md", "bob-jones.md"] },
  { name: "teams", icon: "\uD83D\uDC65", files: ["squad-payments.md", "squad-platform.md"] },
  { name: "topics", icon: "\uD83D\uDCCC", files: ["2026-04-feature-new-checkout.md", "2026-03-api-migration.md"] },
  { name: "discussions", icon: "\uD83D\uDCAC", files: ["2026-04-02-daily-payments.md"] },
  { name: "projects", icon: "\uD83D\uDCC1", files: ["processing-3-0.md", "vault-automation.md"] },
  { name: "fleeting", icon: "\uD83D\uDCDD", files: ["2026-04-09-new-tokenization-service.md"] },
];

export const sampleEntity = {
  filename: "billing-api.md",
  frontmatter: [
    { key: "type", value: "actor" },
    { key: "name", value: "Billing API" },
    { key: "status", value: "active" },
    { key: "domain", value: "payments" },
    { key: "pci", value: "true" },
    { key: "team", value: '["[[squad-payments]]"]' },
    { key: "updated_at", value: "2026-04-15" },
    { key: "updated_by", value: "bedrock@agent" },
  ],
  body: [
    "# Billing API",
    "",
    "> [!danger] PCI Scope",
    "> This actor processes card data and is subject to PCI-DSS compliance.",
    "",
    "Core payment processing service responsible for invoice generation,",
    "payment capture, and settlement. Integrates with [[auth-gateway]]",
    "for token validation and [[notification-service]] for payment",
    "receipts.",
    "",
    "## Dependencies",
    "- [[auth-gateway]] \u2014 token validation",
    "- [[notification-service]] \u2014 email receipts",
    "- [[squad-payments]] \u2014 owning team",
  ],
};
