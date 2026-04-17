import { sampleEntity } from "@/data/vault-demo";

function Wikilink({ children }: { children: string }) {
  return (
    <span className="text-purple-400">[[{children}]]</span>
  );
}

function renderBodyLine(line: string, i: number) {
  // Heading
  if (line.startsWith("# ") || line.startsWith("## ")) {
    const level = line.startsWith("## ") ? "text-sm" : "text-base";
    return (
      <div key={i} className={`${level} font-semibold text-text-primary mt-2`}>
        {line}
      </div>
    );
  }

  // Callout
  if (line.startsWith("> [!")) {
    const isDanger = line.includes("danger");
    return (
      <div
        key={i}
        className={`text-xs px-2 py-1 rounded mt-1 ${
          isDanger
            ? "bg-orange-500/10 text-orange-400 border-l-2 border-orange-500"
            : "bg-purple-500/10 text-purple-400 border-l-2 border-purple-500"
        }`}
      >
        {line.replace(/^>\s*/, "")}
      </div>
    );
  }
  if (line.startsWith("> ")) {
    return (
      <div key={i} className="text-xs px-2 py-0.5 text-text-muted">
        {line.replace(/^>\s*/, "")}
      </div>
    );
  }

  // Empty line
  if (line === "") {
    return <div key={i} className="h-2" />;
  }

  // List item with wikilinks
  if (line.startsWith("- ")) {
    const parts = line.split(/(\[\[[^\]]+\]\])/);
    return (
      <div key={i} className="text-text-secondary flex gap-1">
        <span className="text-text-muted select-none">-</span>
        <span>
          {parts.map((part, j) => {
            const match = part.match(/^\[\[([^\]]+)\]\]$/);
            if (match) return <Wikilink key={j}>{match[1]}</Wikilink>;
            return <span key={j}>{part}</span>;
          })}
        </span>
      </div>
    );
  }

  // Regular text with wikilinks
  const parts = line.split(/(\[\[[^\]]+\]\])/);
  return (
    <div key={i} className="text-text-secondary">
      {parts.map((part, j) => {
        const match = part.match(/^\[\[([^\]]+)\]\]$/);
        if (match) return <Wikilink key={j}>{match[1]}</Wikilink>;
        return <span key={j}>{part}</span>;
      })}
    </div>
  );
}

export function VaultPreview() {
  return (
    <div className="flex-1 min-w-0 rounded-lg border border-border bg-bg-base overflow-hidden">
      {/* Title bar */}
      <div className="flex items-center gap-2 px-3 py-2 bg-bg-elevated border-b border-border text-xs">
        <span className="text-text-muted">actors/</span>
        <span className="text-text-primary font-medium">{sampleEntity.filename}</span>
      </div>

      {/* Content */}
      <div className="p-4 font-mono text-xs leading-5 space-y-0.5 overflow-x-auto">
        {/* Frontmatter */}
        <div className="text-text-muted">---</div>
        {sampleEntity.frontmatter.map((field) => (
          <div key={field.key}>
            <span className="text-purple-400">{field.key}</span>
            <span className="text-text-muted">: </span>
            {field.value.includes("[[") ? (
              <span className="text-orange-400">{field.value}</span>
            ) : (
              <span className="text-success">{field.value}</span>
            )}
          </div>
        ))}
        <div className="text-text-muted">---</div>

        <div className="h-2" />

        {/* Body */}
        {sampleEntity.body.map((line, i) => renderBodyLine(line, i))}
      </div>
    </div>
  );
}
