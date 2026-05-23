import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        paper: "#fbfaf7",
        moss: "#32684f",
        coral: "#d45b45",
        skyline: "#3d6f9f",
      },
      boxShadow: {
        soft: "0 18px 45px rgba(23, 23, 23, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;

