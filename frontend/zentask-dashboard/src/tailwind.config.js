/** @type {import('tailwindcss').Config} */

export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}"
    ],
    theme: {
        extend: {

            colors: {
                primary: "#5c01d5",
                lightgray: "#d4d4d4",
                dark: "#171717",
                dimgray: "#737373"
            },

            fontFamily: {
                inter: ["Inter", "sans-serif"],
                sf: ["SF Pro", "sans-serif"]
            },

            borderRadius: {
                sidebar: "32px"
            }

        }
    },
    plugins: [
        require('@tailwindcss/forms')
    ]
}