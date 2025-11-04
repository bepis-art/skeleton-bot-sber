module.exports = {
    root: true,
    env: {
        es6: true,
        browser: true,
        node: true,
        jest: true
    },
    parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module"
    },
    ignorePatterns: [
        ".eslintrc.cjs",
    ],
    overrides: [
        // === Vue файлы ===
        {
            files: ["*.vue"],
            parser: "vue-eslint-parser",
            parserOptions: {
                parser: "@typescript-eslint/parser", // для <script lang="ts">
                sourceType: "module",
                ecmaVersion: "latest",
                extraFileExtensions: [".vue"]
            },
            plugins: ["vue"],
            rules: {
                curly: ["error", "all"],
                semi: ["error", "always"],
                "indent": ["error", 4],
                "brace-style": ["error", "1tbs", { "allowSingleLine": false }],
                "no-unused-vars": "warn",
                "no-undef": "error",
                "no-console": "warn",
                "@typescript-eslint/no-explicit-any": "off",
                "@typescript-eslint/no-unused-vars": "warn",
                "@typescript-eslint/explicit-function-return-type": "off",
                "@typescript-eslint/no-unsafe-assignment": "off",
                "@typescript-eslint/no-unsafe-member-access": "off"
            }
        },
        // HTML — без extends, только правила
        {
            files: ["*.html", "**/*.html"],
            parser: "@html-eslint/parser",
            plugins: ["@html-eslint"],
            rules: {
                "@html-eslint/no-duplicate-attrs": "error",
                "@html-eslint/no-duplicate-id": "error",
                "@html-eslint/require-li-container": "error",
                "@html-eslint/no-obsolete-tags": "error"
                // остальные — по желанию
            }
        },

        // JS
        {
            files: ["*.js", "**/*.js"],
            env: { node: true, browser: true },
            extends: ["eslint:recommended"],
            rules: {
                curly: ["error", "all"],
                semi: ["error", "always"],
                "indent": ["error", 4],
                "brace-style": ["error", "1tbs", { "allowSingleLine": false }],
                "no-unused-vars": "warn",
                "no-undef": "error",
                "no-console": "warn"
            }
        },

        // TS
        {
            files: ["*.ts", "*.tsx"],
            parser: "@typescript-eslint/parser",
            parserOptions: {
                ecmaVersion: "latest",
                sourceType: "module",
                ecmaFeatures: {
                    jsx: true
                }
            },
            plugins: ["@typescript-eslint"],
            extends: [
                "eslint:recommended",
                "plugin:@typescript-eslint/recommended"
            ],
            rules: {
                curly: ["error", "all"],
                semi: ["error", "always"],
                "indent": ["error", 4],
                "brace-style": ["error", "1tbs", { "allowSingleLine": false }],
                "@typescript-eslint/no-explicit-any": "off",
                "@typescript-eslint/no-unused-vars": "warn",
                "@typescript-eslint/explicit-function-return-type": "off",
                "@typescript-eslint/no-unsafe-assignment": "off",
                "@typescript-eslint/no-unsafe-member-access": "off"
            }
        }
    ]
};