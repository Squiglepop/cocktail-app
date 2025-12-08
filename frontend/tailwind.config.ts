import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        cocktail: {
          amber: '#d97706',
          copper: '#b45309',
          cream: '#fef3c7',
        },
      },
    },
  },
  plugins: [],
}

export default config
