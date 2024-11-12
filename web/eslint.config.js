import pluginReact from "eslint-plugin-react"
import globals from "globals"
import tseslint from "typescript-eslint"

import pluginJs from "@eslint/js"

/** @type {import('eslint').Linter.Config[]} */
export default [
  {
    files: ["**/*.{js,mjs,cjs,ts,jsx,tsx}"],
  },
  { ignores: ["build/**", ".react-router/**", "playground.ts"] },
  { languageOptions: { globals: globals.browser } },
  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
  // important change from the default
  pluginReact.configs.flat["jsx-runtime"],
  // https://typescript-eslint.io/rules/no-unused-vars/
  {
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          args: "all",
          argsIgnorePattern: "^_",
          caughtErrors: "all",
          caughtErrorsIgnorePattern: "^_",
          destructuredArrayIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          ignoreRestSiblings: true,
        },
      ],
    },
  },
]
