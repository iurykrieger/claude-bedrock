import { SectionHeader } from "@/components/section-header";
import { VaultSidebar } from "@/components/vault-sidebar";
import { VaultPreview } from "@/components/vault-preview";

export function VaultDemo() {
  return (
    <section id="vault-demo" className="py-24 bg-bg-card border-t border-border">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeader
          label="The Output"
          title="Your vault, visualized"
          subtitle="See how Bedrock organizes your knowledge into a structured, navigable graph in Obsidian."
        />

        <div className="mt-14 flex flex-col md:flex-row gap-4">
          <VaultSidebar />
          <VaultPreview />
        </div>

        {/* Videos: vault navigation + graph view */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-lg border border-border bg-bg-base overflow-hidden">
            <div className="px-3 py-2 bg-bg-elevated border-b border-border text-xs text-text-muted">
              Navigating entities
            </div>
            <video
              src="/videos/vault-navigation.mp4"
              autoPlay
              loop
              muted
              playsInline
              className="w-full"
            />
          </div>
          <div className="rounded-lg border border-border bg-bg-base overflow-hidden">
            <div className="px-3 py-2 bg-bg-elevated border-b border-border text-xs text-text-muted">
              Knowledge graph
            </div>
            <video
              src="/videos/graph-view.mp4"
              autoPlay
              loop
              muted
              playsInline
              className="w-full"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
