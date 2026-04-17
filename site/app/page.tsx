import { Hero } from "@/components/hero";
import { HowItWorks } from "@/components/how-it-works";
import { SkillsShowcase } from "@/components/skills-showcase";
import { UseCases } from "@/components/use-cases";
import { VaultDemo } from "@/components/vault-demo";
import { Installation } from "@/components/installation";
import { AnimateIn } from "@/components/animate-in";

export default function Home() {
  return (
    <>
      <Hero />

      <AnimateIn>
        <HowItWorks />
      </AnimateIn>

      <AnimateIn>
        <SkillsShowcase />
      </AnimateIn>

      <AnimateIn>
        <UseCases />
      </AnimateIn>

      <AnimateIn>
        <VaultDemo />
      </AnimateIn>

      <AnimateIn>
        <Installation />
      </AnimateIn>
    </>
  );
}
