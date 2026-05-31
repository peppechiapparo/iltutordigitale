/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Token brand — fonte: docs/06-BRAND.md
        brand: {
          blue: '#185FA5',
          'blue-mid': '#378ADD',
          'blue-light': '#E6F1FB',
          orange: '#EF9F27',
          'orange-dk': '#BA7517',
          'orange-lt': '#FAC775',
          dark: '#2C2C2A',
          mid: '#888780',
          bg: '#F1EFE8',
        },
      },
      fontFamily: {
        // Inter (corpo), Nunito (titoli) — vedi docs/06-BRAND.md
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Nunito', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        // Scala accessibile per pubblico over 45 — mai sotto 13px
        base: ['17px', '1.7'],
        lg: ['19px', '1.65'],
        xl: ['22px', '1.5'],
      },
    },
  },
  plugins: [],
};
