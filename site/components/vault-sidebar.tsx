"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { vaultFolders } from "@/data/vault-demo";

export function VaultSidebar({ onFileSelect }: { onFileSelect?: (file: string) => void }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    actors: true,
  });

  function toggleFolder(name: string) {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  }

  return (
    <div className="w-full md:w-56 shrink-0 rounded-lg border border-border bg-bg-base p-3 font-mono text-xs overflow-hidden">
      <div className="text-text-muted mb-2 px-1 text-[10px] uppercase tracking-wider">
        Vault
      </div>
      {vaultFolders.map((folder) => (
        <div key={folder.name}>
          <button
            onClick={() => toggleFolder(folder.name)}
            className={cn(
              "flex items-center gap-1.5 w-full px-1.5 py-1 rounded text-left transition-colors",
              "hover:bg-bg-elevated text-text-secondary",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500"
            )}
          >
            <span className="text-[10px] text-text-muted select-none">
              {expanded[folder.name] ? "\u25BE" : "\u25B8"}
            </span>
            <span>{folder.icon}</span>
            <span>{folder.name}/</span>
          </button>
          {expanded[folder.name] && (
            <div className="ml-5 border-l border-border/50 pl-2">
              {folder.files.map((file) => (
                <button
                  key={file}
                  onClick={() => onFileSelect?.(file)}
                  className={cn(
                    "block w-full text-left px-1.5 py-0.5 rounded truncate transition-colors",
                    "text-text-muted hover:text-purple-400 hover:bg-purple-500/5",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500",
                    file === "billing-api.md" && "text-purple-400 bg-purple-500/5"
                  )}
                >
                  {file}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
