import localFont from "next/font/local";
import { Inter, JetBrains_Mono } from "next/font/google";

export const satoshi = localFont({
  src: [
    { path: "./fonts/satoshi/Satoshi-Regular.woff2", weight: "400", style: "normal" },
    { path: "./fonts/satoshi/Satoshi-Medium.woff2", weight: "500", style: "normal" },
    { path: "./fonts/satoshi/Satoshi-Bold.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-satoshi",
  display: "swap",
  preload: true,
});

export const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  display: "swap",
  preload: false,
});
