/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        capgemini: {
          blue: '#0066CC',
          darkblue: '#003366',
          lightblue: '#E6F2FF',
          gray: '#F5F5F5'
        }
      }
    },
  },
  plugins: [],
}