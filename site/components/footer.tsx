import { Star } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border bg-bg-base py-16">
      <div className="max-w-5xl mx-auto px-6 text-center">
        {/* GitHub Star */}
        <a
          href="https://github.com/iurykrieger/claude-bedrock"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2.5 rounded-xl border border-border bg-bg-card px-6 py-3 text-sm font-medium text-text-secondary transition-all duration-200 hover:border-border-hover hover:text-text-primary hover:shadow-md mb-8"
        >
          <Star className="w-4 h-4" />
          Star on GitHub
        </a>

        {/* Meta */}
        <div className="text-xs text-text-muted leading-7">
          <div className="flex items-center justify-center gap-2 flex-wrap">
            <span>MIT License</span>
            <span className="text-border hidden sm:inline">&middot;</span>
            <span>
              Built by{" "}
              <a
                href="https://github.com/iurykrieger"
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-secondary hover:text-purple-400 transition-colors"
              >
                Iury Krieger
              </a>
            </span>
          </div>
          <div className="flex items-center justify-center gap-2 flex-wrap mt-1">
            <span>Powered by</span>
            <a
              href="https://obsidian.md"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-secondary hover:text-purple-400 transition-colors"
            >
              Obsidian
            </a>
            <span>+</span>
            <a
              href="https://docs.anthropic.com/en/docs/claude-code"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-secondary hover:text-purple-400 transition-colors"
            >
              Claude Code
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
