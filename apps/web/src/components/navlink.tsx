"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

export default function NavLink({ href, children }: { href: string; children: ReactNode }) {
  const pathname = usePathname();
  const active = pathname === href;

  return (
    <Link
      href={href}
      className={[
        "block rounded-md px-3 py-2 text-sm transition",
        active
          ? "bg-base-2 border-moss/60 border text-neutral-50"
          : "hover:bg-base-2/70 border border-transparent text-neutral-300 hover:text-neutral-50",
      ].join(" ")}
    >
      {children}
    </Link>
  );
}
