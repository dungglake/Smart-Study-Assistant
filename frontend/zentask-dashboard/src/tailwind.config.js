/** @type {import('tailwindcss').Config} */
module.exports = {
    "content": [
        "./src/**/*.{js,jsx,ts,tsx,vue}"
    ],
    "theme": {
        "extend": {
            "colors": {
                "white": "#fff",
                "lightgray": "#d4d4d4",
                "darkslategray": "#404040",
                "gray": "#171717",
                "mediumblue": "#5c01d5",
                "dimgray": "#737373"
            },
            "fontFamily": {
                "inter": "Inter",
                "sf-pro": "SF Pro"
            },
            "borderRadius": {
                "num-6": "6px"
            },
            "padding": {
                "num-12": "12px",
                "num-10": "10px"
            }
        },
        "fontSize": {
            "num-14": "14px"
        },
        "lineHeight": {
            "num-20": "20px"
        }
    },
    "corePlugins": {
        "preflight": false
    }
}