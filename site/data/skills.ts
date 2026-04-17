export interface Skill {
  id: string;
  name: string;
  command: string;
  shortDescription: string;
  description: string;
  icon: string;
  videoPath: string;
}

export const skills: Skill[] = [
  {
    id: "setup",
    name: "setup",
    command: "/bedrock:setup",
    shortDescription: "Initialize vault structure and templates",
    description:
      "Interactive vault initialization and configuration. Guides you through language selection, dependency checks, vault objective, and scaffolds directories, templates, config, and connected example entities.",
    icon: "\u2699",
    videoPath: "/videos/setup.mp4",
  },
  {
    id: "teach",
    name: "teach",
    command: "/bedrock:teach",
    shortDescription: "Ingest from Confluence, GDocs, GitHub",
    description:
      "Ingest external sources — feed it a Confluence page, Google Doc, GitHub repo, or CSV. It extracts entities and writes them to your vault via /bedrock:preserve.",
    icon: "\uD83D\uDCDA",
    videoPath: "/videos/teach.mp4",
  },
  {
    id: "preserve",
    name: "preserve",
    command: "/bedrock:preserve",
    shortDescription: "Create entities with bidirectional links",
    description:
      "Single write point for all entities. Detects type, matches existing files, creates or updates with bidirectional wikilinks and structured frontmatter.",
    icon: "\uD83D\uDD17",
    videoPath: "/videos/preserve.mp4",
  },
  {
    id: "ask",
    name: "ask",
    command: "/bedrock:ask",
    shortDescription: "Search and cross-reference your vault",
    description:
      "Orchestrated vault reader — decomposes questions, searches the graph and vault, cross-references entities, and builds structured answers with wikilinks.",
    icon: "\uD83D\uDD0D",
    videoPath: "/videos/ask.mp4",
  },
  {
    id: "compress",
    name: "compress",
    command: "/bedrock:compress",
    shortDescription: "Deduplicate and consolidate entities",
    description:
      "Deduplication and vault health. Finds duplicates, orphan entities, broken links, and stale content. Consolidates and reports vault health.",
    icon: "\u2696",
    videoPath: "/videos/compress.mp4",
  },
  {
    id: "sync",
    name: "sync",
    command: "/bedrock:sync",
    shortDescription: "Re-sync with external sources",
    description:
      "Re-sync entities with their external sources. Supports GitHub activity, contributor profiles, and source metadata updates.",
    icon: "\uD83D\uDD04",
    videoPath: "/videos/sync.mp4",
  },
];
