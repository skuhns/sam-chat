"use client";

import { useEffect } from "react";
import NavLink from "./navlink";
import { useLocalStorage } from "../app/hooks/useLocalStorage";

export function Sidebar() {
  const [open, setOpen] = useLocalStorage<boolean>("ui:sidebar-open", true);

  // Close sidebar by default on very small screens (first load)
  useEffect(() => {
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setOpen(false);
    }
  }, []);

  const width = open ? "w-64" : "w-14";

  return (
    <aside
      className={[
        "group fixed z-40 h-dvh shrink-0 border-r border-neutral-600/50 backdrop-blur md:static md:z-auto",
        "transition-[width] duration-200 ease-out",
        width,
      ].join(" ")}
      aria-label="Primary"
    >
      <div className="flex h-full flex-col p-3">
        <div className="mb-4 flex items-center justify-between">
          <div
            className={[
              "overflow-hidden transition-[width,opacity] duration-200",
              open ? "w-auto opacity-100" : "w-0 opacity-0",
            ].join(" ")}
          >
            <span className="font-display text-lg">Waypoint</span>
          </div>

          <SidebarToggle isOpen={open} onToggle={() => setOpen((v) => !v)} />
        </div>

        {/* Nav */}
        <nav className="space-y-1">
          <NavLink href="/">Home</NavLink>
          <NavLink href="/projects">Projects</NavLink>
          <NavLink href="/blog">Blog</NavLink>
          <NavLink href="/travel">Travel</NavLink>
          <NavLink href="/about">About</NavLink>
          <NavLink href="/recruiters">For Recruiters</NavLink>
        </nav>

        {/* Footer / status */}
        <div className="mt-auto pt-4">
          <div
            className={[
              "bg-base-2/50 rounded-lg border border-neutral-600/50 p-3 text-xs text-neutral-300",
              open ? "" : "hidden",
            ].join(" ")}
          >
            Tip: Press <kbd className="bg-base-2 rounded px-1">[</kbd> to toggle.
          </div>
        </div>
      </div>

      {/* Keyboard shortcut: "[" toggles */}
      <Keybind keyChar="[" onPress={() => setOpen((v) => !v)} />
    </aside>
  );
}

function Keybind({ keyChar, onPress }: { keyChar: string; onPress: () => void }) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === keyChar && !e.metaKey && !e.ctrlKey && !e.altKey) {
        e.preventDefault();
        onPress();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [keyChar, onPress]);

  return null;
}

type SidebarToggleProps = {
  isOpen: boolean;
  onToggle: () => void;
};

export function SidebarToggle({ isOpen, onToggle }: SidebarToggleProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={isOpen}
      aria-label={isOpen ? "Collapse sidebar" : "Expand sidebar"}
      className="bg-base-2/70 hover:border-moss/70 hover:bg-base-2 inline-flex items-center gap-2 rounded-lg border border-neutral-600/60 px-3 py-2 text-neutral-50 transition"
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        className={`transition-transform ${isOpen ? "" : "-rotate-180"}`}
        aria-hidden="true"
      >
        <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
    </button>
  );
}
