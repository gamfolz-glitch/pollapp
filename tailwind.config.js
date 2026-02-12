/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./polls/templates/**/*.html",
    "templates/**/*.html",
    "./static/js/**/*.js",  // если будет JS
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4f46e5',       // indigo-600
        'primary-dark': '#3730a3', // indigo-700
        'accent': '#7c3aed',       // violet-600
        'success': '#10b981',      // emerald-500
        'danger': '#ef4444',       // red-500
        'warning': '#f59e0b',      // amber-500
        'info': '#0ea5e9',         // sky-500
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
      },
      keyframes: {
        slideIn: {
          '0%': { opacity: 0, transform: 'translateX(-20px)' },
          '100%': { opacity: 1, transform: 'translateX(0)' },
        },
      },
      animation: {
        'slide-in': 'slideIn 0.4s ease-out',
      },
    },
  },
  plugins: [],
}