/**
 * This is a minimal config for Tailwind CSS v3 for Django Tailwind
 *
 */

module.exports = {
  content: [
    '../templates/**/*.html',
    '../../templates/**/*.html',
    '../../**/templates/**/*.html',
    '../../**/templates/**/*.html',
    './src/**/*.{js,jsx,ts,tsx,vue,svelte,elm,php,python}',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}

