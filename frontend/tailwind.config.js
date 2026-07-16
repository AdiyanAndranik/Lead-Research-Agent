/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: '#0A0A0F',
        surface: '#13131A',
        's2': '#1E1E2A',
        border: '#2A2A3A',
        accent: '#6366F1',
        green: '#10B981',
        amber: '#F59E0B',
        red: '#EF4444',
        't1': '#E8E8F0',
        't2': '#9090A8',
        't3': '#5A5A72',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}