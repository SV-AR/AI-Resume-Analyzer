export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1e293b",
        desk: "#f8fafc",
        margin: "#2563eb",
        mark: "#dbeafe",
        redpen: "#dc2626",
        pass: "#16a34a",
        warning: "#d97706",
        slate2: "#64748b",
        rule: "#e2e8f0",
      },
      fontFamily: {
        serif: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
