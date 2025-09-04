import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/pages/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Bases
        base: {
          DEFAULT: "#0F0E0E",  // main background
          2: "#1C1B1A",        // section contrast
        },
        // Neutrals
        neutral: {
          50:  "#E6E2DC",      // primary text
          300: "#B9B1A7",      // secondary text
          600: "#5C5A57",      // borders/dividers
        },
        // Accents
        amber:  { DEFAULT: "#D97706" }, // CTA / hover
        moss:   { DEFAULT: "#A3BE8C" }, // links / accents
        clay:   { DEFAULT: "#E07A5F" }, // subtle emphasis
        teal:   { DEFAULT: "#468189" }, // secondary accent
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-satoshi)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderColor: {
        DEFAULT: "#5C5A57",
      },
    },
  },
  plugins: [],
};

export default config;