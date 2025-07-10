/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e8f4fd',
          100: '#d1e9fb',
          200: '#a3d3f7',
          300: '#75bdf3',
          400: '#47a7ef',
          500: '#1991eb',
          600: '#1474bc',
          700: '#0f578d',
          800: '#0a3a5e',
          900: '#051d2f'
        },
        secondary: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12'
        },
        medical: {
          blue: '#1991eb',
          orange: '#f97316',
          lightblue: '#e8f4fd',
          gray: '#6b7280'
        }
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}