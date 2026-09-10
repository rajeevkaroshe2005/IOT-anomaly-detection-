/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Required Primary Industrial Palette
        primary: {
          DEFAULT: "#16423C", // Deep Forest Green
          dark: "#0F2F2B",
          light: "#1F5C54",   // Dark Teal
        },
        teal: {
          industrial: "#1F5C54",
        },
        // Required Secondary Industrial Palette
        amber: {
          industrial: "#D99A2B", // Warm Amber
        },
        orange: {
          burnt: "#C96B32",      // Burnt Orange (Temperature)
        },
        // Required Backgrounds
        bg: {
          offwhite: "#F5F1E8",   // Warm Off-White
          beige: "#E9E2D3",      // Soft Beige
        },
        // Required Surfaces
        surface: {
          white: "#FFFFFF",
          sand: "#F0EBE1",       // Light Sand
        },
        // Required Text
        text: {
          charcoal: "#242424",   // Dark Charcoal
          muted: "#686868",      // Secondary Gray
        },
        // Required Status Indicators
        status: {
          normal: "#2E7D32",     // Normal Green
          warning: "#D99A2B",    // Warning Amber
          critical: "#B23A2F",   // Critical Dark Red / Anomaly
          offline: "#6B6B6B",    // Offline Gray
        }
      },
      fontFamily: {
        sans: ['"Inter"', '"IBM Plex Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace']
      },
      boxShadow: {
        'industrial': '0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)',
        'industrial-md': '0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04)'
      }
    },
  },
  plugins: [],
}
