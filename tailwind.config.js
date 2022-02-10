/**
 * Tailwind configuration file.
 *
 * @see https://tailwindcss.com/docs/configuration
 */
module.exports = {
  purge: {
    content: [
      './assets/**/*.js',
      './templates/**/*.{html,tsx}',
      './apps/*/templates/**/*.html',
      './apps/*/javascript/**/*.tsx',
    ],
    options: {
      /** Dynamic colors on website landing page */
      safelist: [/(bg|border|text)-(indigo|green|yellow)-\d00/],
    },
  },
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
        10: 'var(--c-gray-10)',
        // Website colors
        100: 'var(--c-gray-100)',
        200: 'var(--c-gray-200)',
        300: 'var(--c-gray-300)',
        400: 'var(--c-gray-400)',
        500: 'var(--c-gray-500)',
        600: 'var(--c-gray-600)',
        700: 'var(--c-gray-700)',
        800: 'var(--c-gray-800)',
        900: 'var(--c-gray-900)',
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
        // Website colors
        100: 'var(--c-green-100)',
        200: 'var(--c-green-200)',
        300: 'var(--c-green-300)',
        400: 'var(--c-green-400)',
        500: 'var(--c-green-500)',
        600: 'var(--c-green-600)',
        700: 'var(--c-green-700)',
        800: 'var(--c-green-800)',
        900: 'var(--c-green-900)',
      },
      red: {
        DEFAULT: 'var(--c-red)',
        50: 'var(--c-red-50)',
        20: 'var(--c-red-20)',
        10: 'var(--c-red-10)',
      },
      transparent: 'var(--c-transparent)',
      // website migration
      // Generated automatically https://tailwind.ink/
      // We are using indigo as primary color to make it faster to prototype
      // with Tailwind Components
      indigo: {
        50: 'var(--c-indigo-50)',
        100: 'var(--c-indigo-100)',
        200: 'var(--c-indigo-200)',
        300: 'var(--c-indigo-300)',
        400: 'var(--c-indigo-400)',
        500: 'var(--c-indigo-500)',
        600: 'var(--c-indigo-600)',
        700: 'var(--c-indigo-700)',
        800: 'var(--c-indigo-800)',
        900: 'var(--c-indigo-900)',
      },
      yellow: {
        50: 'var(--c-yellow-500)',
        100: 'var(--c-yellow-100)',
        200: 'var(--c-yellow-200)',
        300: 'var(--c-yellow-300)',
        400: 'var(--c-yellow-400)',
        500: 'var(--c-yellow-500)',
        600: 'var(--c-yellow-600)',
        700: 'var(--c-yellow-700)',
        800: 'var(--c-yellow-800)',
        900: 'var(--c-yellow-900)',
      },
    },
    extend: {
      flex: {
        2: '2 2 0%',
      },
    },
    container: {
      center: true,
    },
  },
  variants: {
    extend: {},
  },
  corePlugins: {
    preflight: true, // To be removed in the future before deprecating Tailwind.

    // Disabling ring as it pollutes dev tools with CSS variables.
    ringWidth: false,
    ringColor: false,
    ringOpacity: false,
    ringOffsetWidth: false,
    ringOffsetColor: false,
  },
  plugins: [
    // TODO: decide whether to replace with native prose class for typography
    require('@tailwindcss/typography'),
  ],
}
