/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        levi: {
          bg: "#050608",
          panel: "rgba(10, 14, 23, 0.45)",
          cyan: "#00f3ff",
          violet: "#8b5cf6",
          amber: "#f59e0b",
          coral: "#ef4444",
          emerald: "#10b981",
        }
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["Inter", "sans-serif"]
      }
    },
  },
  plugins: [],
}
