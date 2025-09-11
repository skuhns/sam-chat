import "./globals.css";

import { type Metadata } from "next";
import { inter, jetbrainsMono, satoshi } from "./fonts";
import { TRPCReactProvider } from "trpc/react";
import { Sidebar } from "components/sidebar";
import Header from "components/header";
import BackgroundMap from "components/background";
import PMTilesProvider from "./providers/pmtiles";
import Assistant from "components/chat/assistant";

export const metadata: Metadata = {
  title: "Sam Kuhns",
  description: "Full-stack developer, outdoor enthusiast.",
  icons: [{ rel: "icon", url: "/favicon.ico" }],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <PMTilesProvider />
      <TRPCReactProvider>
        <body className="min-h-dvh font-sans text-neutral-50 antialiased">
          <div className="pointer-events-none -z-10" aria-hidden>
            <BackgroundMap location="chicago" darken={0.4} blurPx={4} interactive={false} />
          </div>
          <div className="pointer-events-auto relative z-10 flex min-h-dvh justify-center">
            <div className="w-full md:w-[70%]">{<Assistant />}</div>
          </div>
          <div>{children}</div>
          {/* <div className="flex">
            <Sidebar />
            <div className="flex min-h-dvh w-full flex-col pl-14 md:pl-0">
              <Header />
              <main className="mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
            </div>
          </div> */}
        </body>
      </TRPCReactProvider>
    </html>
  );
}
