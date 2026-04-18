import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // CiteGuard severity colors (§5.7)
        // NEVER green for severity
        severity: {
          critical: { DEFAULT: "#EF4444", bg: "#FEF2F2" },
          high:     { DEFAULT: "#F97316", bg: "#FFF7ED" },
          medium:   { DEFAULT: "#EAB308", bg: "#FEFCE8" },
          advisory: { DEFAULT: "#3B82F6", bg: "#EFF6FF" },
        },
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "-apple-system", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
