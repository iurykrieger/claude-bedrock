"use client";

import { useEffect, useState } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { label: "How It Works", href: "#how-it-works" },
  { label: "Skills", href: "#skills" },
  { label: "Use Cases", href: "#use-cases" },
  { label: "Install", href: "#install" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 50);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-6 transition-all duration-300",
        "backdrop-blur-xl",
        scrolled
          ? "bg-bg-base/80 border-b border-border shadow-[0_1px_8px_rgba(0,0,0,0.3)]"
          : "bg-transparent border-b border-transparent"
      )}
    >
      {/* Logo */}
      <a href="#" className="flex items-center gap-2.5 text-text-primary font-semibold text-sm tracking-tight">
        <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5">
          <circle cx="12" cy="12" r="3" fill="#a882ff" />
          <circle cx="4" cy="6" r="1.5" fill="#e8754a" />
          <circle cx="20" cy="6" r="1.5" fill="#a882ff" />
          <circle cx="4" cy="18" r="1.5" fill="#a882ff" />
          <circle cx="20" cy="18" r="1.5" fill="#e8754a" />
          <line x1="12" y1="12" x2="4" y2="6" stroke="#a882ff" strokeWidth="0.5" opacity="0.4" />
          <line x1="12" y1="12" x2="20" y2="6" stroke="#a882ff" strokeWidth="0.5" opacity="0.4" />
          <line x1="12" y1="12" x2="4" y2="18" stroke="#a882ff" strokeWidth="0.5" opacity="0.4" />
          <line x1="12" y1="12" x2="20" y2="18" stroke="#e8754a" strokeWidth="0.5" opacity="0.4" />
        </svg>
        Bedrock
      </a>

      {/* Links */}
      <div className="hidden md:flex items-center gap-6">
        {NAV_LINKS.map((link) => (
          <a
            key={link.href}
            href={link.href}
            className="text-text-muted text-[13px] hover:text-text-primary transition-colors"
          >
            {link.label}
          </a>
        ))}
      </div>

      {/* GitHub Badge */}
      <a
        href="https://github.com/iurykrieger/claude-bedrock"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 rounded-lg border border-border bg-bg-elevated/50 px-3 py-1.5 text-xs text-text-secondary hover:border-border-hover hover:text-text-primary transition-colors"
      >
        <Star className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">Star on GitHub</span>
      </a>
    </nav>
  );
}
