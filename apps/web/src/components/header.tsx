export default function Header() {
  return (
    <header className="bg-base/70 sticky top-0 z-30 border-b border-neutral-600/50 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <span className="bg-moss shadow-moss/30 h-2 w-2 rounded-full shadow-[0_0_8px]" />
          <span className="font-display">Sam Kuhns</span>
        </div>
        <nav className="hidden items-center gap-4 text-sm text-neutral-300 md:flex">
          <a href="/resume.pdf" className="hover:text-neutral-50">
            Resume
          </a>
          <a href="/contact" className="hover:text-neutral-50">
            Contact
          </a>
        </nav>
      </div>
    </header>
  );
}
