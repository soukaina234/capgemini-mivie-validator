/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'capgemini-blue': '#0066CC',
        'capgemini-darkblue': '#003366',
        'capgemini-lightblue': '#E6F2FF',
      },
    },
  },
  plugins: [],
}