/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0284c7',
          600: '#0369a1',
          700: '#075985',
          800: '#0c4a6e',
          900: '#082f49',
        },
        sif: {
          high: '#dc2626',      // Red-600
          medium: '#d97706',    // Amber-600
          low: '#059669',       // Emerald-600
          disagreement: '#7c3aed' // Violet-600
        }
      },
    },
  },
  plugins: [],
}

