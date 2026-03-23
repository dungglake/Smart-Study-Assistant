/** @type {import('tailwindcss').Config} */

export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}"
    ],
    safelist: [
        'bg-red-500',
        'bg-yellow-500',
        'bg-green-600',
        'bg-[#e5e5e5]',
    ],
    theme: {
        extend: {

            colors: {
                primary: "#5c01d5",
                lightgray: "#d4d4d4",
                dark: "#171717",
                dimgray: "#737373",
                tomato: "#f73131",
                white: "#fff",
                darkslategray: "#404040",
                mediumblue: "#5c01d5"
            },

            fontFamily: {
                inter: ["Inter", "sans-serif"],
                sf: ["SF Pro", "sans-serif"]
            },

            borderRadius: {
                sidebar: "32px"
            },

            "padding": {
                "num-0": "0px"
            },

            "fontSize": {
                "num-16": "16px"
            },

            "lineHeight": {
                "num-24": "24px"
            }
        },
    },
    plugins: [
        require('@tailwindcss/forms')
    ]
}