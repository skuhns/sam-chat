import "./globals.css";

import { type Metadata } from "next";
import { inter, jetbrainsMono, satoshi } from "./fonts";
import { TRPCReactProvider } from "trpc/react";
import { Sidebar } from "components/sidebar";
import Header from "components/header";
import BackgroundMap from "components/background";

export const metadata: Metadata = {
  title: "Sam Kuhns",
  description: "Full-stack developer, outdoors enthusiast.",
  icons: [{ rel: "icon", url: "/favicon.ico" }],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <TRPCReactProvider>
        <body className="min-h-dvh font-sans text-neutral-50 antialiased">
          <BackgroundMap
            location="chicago"
            darken={0.4}
            blurPx={0} // try 2–4 if your foreground fights the lines
            interactive={false}
          />
          <div className="flex">
            <Sidebar />
            <div className="flex min-h-dvh w-full flex-col pl-14 md:pl-0">
              <Header />
              <main className="mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
            </div>
          </div>
        </body>
      </TRPCReactProvider>
    </html>
  );
}
