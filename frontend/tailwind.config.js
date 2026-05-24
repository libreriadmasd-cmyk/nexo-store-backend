/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Poppins"', "system-ui", "sans-serif"],
        display: ['"Poppins"', "system-ui", "sans-serif"],
        rounded: ['"Poppins"', "system-ui", "sans-serif"],
        serif: ['"Poppins"', "system-ui", "sans-serif"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        // Brand Nexo Store
        brand: {
          blue: "#1E3A5F",
          "blue-dark": "#152841",
          blueDark: "#152841",
          teal: "#2EC4B6",
          "teal-dark": "#26A599",
          tealDark: "#26A599",
          coral: "#FF6B6B",
          "coral-dark": "#E45555",
          coralDark: "#E45555",
          yellow: "#FFB703",
          "yellow-dark": "#E0A002",
          yellowDark: "#E0A002",
          cream: "#FAFAF7",
          ink: "#1E3A5F",
          // Legacy aliases (keep components working without rewriting them)
          green: "#2EC4B6",
          "green-dark": "#26A599",
          greenDark: "#26A599",
        },
        // Pasteles soft para badges
        pastel: {
          sand: "#F3EDE3",
          mint: "#D7F3F0",
          lilac: "#E8E2F0",
          butter: "#FFE8B4",
          sky: "#D6E4F2",
          coral: "#FFE0E0",
        },
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "cart-pulse": {
          "0%": { transform: "scale(1)" },
          "40%": { transform: "scale(1.35)" },
          "100%": { transform: "scale(1)" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "cart-pulse": "cart-pulse 450ms ease-out",
        "fade-up": "fade-up 350ms ease-out both",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
