module.exports = {
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
  },
  extends: [
    'plugin:@typescript-eslint/recommended',
    'prettier/@typescript-eslint',
    'plugin:prettier/recommended',
  ],
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'max-len': ['error', { code: 100, ignoreComments: true, ignoreStrings: true }],
    'no-console': 'warn',
    'curly': ['error', 'all'],
    'eqeqeq': ['error', 'always'],
    'prefer-const': 'error',
    'prefer-template': 'error',
    'no-nested-ternary': 'error',
    'no-duplicate-imports': 'error',
  },
  settings: {
    'import/resolver': {
      typescript: {},
    },
  },
}; 