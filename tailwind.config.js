/**
 * Tailwind configuration file.
 *
 * @see https://tailwindcss.com/docs/configuration
 */
module.exports = {
  purge: ["./assets/**/*.js", "./templates/**/*.html"],
  darkMode: false,
  theme: {
    extend: {},
    container: {
      center: true,
    },
  },
  variants: {
    extend: {},
  },
  plugins: [],
};
