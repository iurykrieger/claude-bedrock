import { SectionHeader } from "@/components/section-header";
import { useCases } from "@/data/use-cases";

export function UseCases() {
  return (
    <section id="use-cases" className="py-24 border-t border-border">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeader
          label="Built For"
          title="Your knowledge, structured"
          subtitle="Bedrock adapts to any team or individual workflow where knowledge sprawl is a problem."
        />

        <div className="mt-14 grid grid-cols-1 md:grid-cols-2 gap-4">
          {useCases.map((useCase) => (
            <div
              key={useCase.title}
              className="group rounded-xl border border-border bg-bg-card p-7 transition-all duration-200 hover:border-border-hover hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(0,0,0,0.15)]"
            >
              <span className="text-2xl block mb-4">{useCase.icon}</span>
              <h3 className="text-base font-semibold mb-2">{useCase.title}</h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                {useCase.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
