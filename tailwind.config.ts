import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: "#0d1117",
          fg: "#c9d1d9",
          border: "#30363d",
          accent: "#58a6ff",
          success: "#3fb950",
          error: "#f85149",
          warning: "#d29922",
        },
      },
    },
  },
  plugins: [],
};
export default config;

