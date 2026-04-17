export interface UseCase {
  icon: string;
  title: string;
  description: string;
}

export const useCases: UseCase[] = [
  {
    icon: "\uD83D\uDCBB",
    title: "Engineering Team Wiki",
    description:
      "Track systems, APIs, services, and team knowledge. Every repo becomes an entity with owners, dependencies, and status \u2014 automatically linked.",
  },
  {
    icon: "\uD83D\uDCCA",
    title: "Product Management",
    description:
      "Capture decisions, roadmaps, and cross-team context. Bridge notes connect people to projects to the discussions that shaped them.",
  },
  {
    icon: "\uD83C\uDF10",
    title: "Open Source Project",
    description:
      "Document contributors, architecture decisions, and discussions. Ingest from GitHub PRs and issues directly into structured entities.",
  },
  {
    icon: "\uD83E\uDDE0",
    title: "Personal Second Brain",
    description:
      "Fleeting ideas get captured, promoted to permanent notes, and linked into your growing knowledge graph. Zettelkasten principles, automated.",
  },
];
