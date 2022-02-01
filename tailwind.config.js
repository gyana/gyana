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
        10: 'var(--c-gray-10)',
        // website migration
        100: '#f3f4f6',
        200: '#e5e7eb',
        300: '#d1d5db',
        400: '#9ca3af',
        500: '#6b7280',
        600: '#4b5563',
        700: '#374151',
        800: '#1f2937',
        900: '#111827',
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
        // website migration
        100: '#dcfce7',
        200: '#bbf7d0',
        300: '#86efac',
        400: '#4ade80',
        500: '#22c55e',
        600: '#16a34a',
        700: '#15803d',
        800: '#166534',
        900: '#14532d',
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
        50: '#f6fbfd',
        100: '#e8f7fd',
        200: '#c5e6fb',
        300: '#9ecefb',
        400: '#69a2fb',
        500: '#3874fa',
        600: '#2550f5',
        700: '#203fe0',
        800: '#1a31af',
        900: '#152887',
      },
      yellow: {
        50: '#fefce8',
        100: '#fef9c3',
        200: '#fef08a',
        300: '#fde047',
        400: '#facc15',
        500: '#eab308',
        600: '#ca8a04',
        700: '#a16207',
        800: '#854d0e',
        900: '#713f12',
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
