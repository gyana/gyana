/**
 * Tailwind configuration file.
 *
 * @see https://tailwindcss.com/docs/configuration
 */
module.exports = {
  purge: [
    './assets/**/*.js',
    './templates/**/*.{html,tsx}',
    './apps/*/templates/**/*.html',
    './apps/*/javascript/**/*.tsx',
  ],
  darkMode: false,
  theme: {
    /** All color are CSS variables set in `_colors.scss`. */
    colors: {
      black: {
        DEFAULT: 'var(--c-black)',
        50: 'var(--c-black-50)',
        20: 'var(--c-black-20)',
        10: 'var(--c-black-10)',
      },
      white: {
        DEFAULT: 'var(--c-white)',
      },
      gray: {
        DEFAULT: 'var(--c-gray)',
        50: 'var(--c-gray-50)',
        20: 'var(--c-gray-20)',
        20: 'var(--c-gray-10)',
      },
      blue: {
        DEFAULT: 'var(--c-blue)',
        50: 'var(--c-blue-50)',
        20: 'var(--c-blue-20)',
        10: 'var(--c-blue-10)',
      },
      pink: {
        DEFAULT: 'var(--c-pink)',
        50: 'var(--c-pink-50)',
        20: 'var(--c-pink-20)',
        10: 'var(--c-pink-10)',
      },
      orange: {
        DEFAULT: 'var(--c-orange)',
        50: 'var(--c-orange-50)',
        20: 'var(--c-orange-20)',
        10: 'var(--c-orange-10)',
      },
      green: {
        DEFAULT: 'var(--c-green)',
        50: 'var(--c-green-50)',
        20: 'var(--c-green-20)',
        10: 'var(--c-green-10)',
      },
      red: {
        DEFAULT: 'var(--c-red)',
        50: 'var(--c-red-50)',
        20: 'var(--c-red-20)',
        10: 'var(--c-red-10)',
      },
      transparent: 'var(--c-transparent)',
    },
    extend: {},
    container: {
      center: true,
    },
  },
  variants: {
    extend: {},
  },
  corePlugins: {
    preflight: true // To be removed in the future before deprecating Tailwind.
  },
  plugins: [],
}
