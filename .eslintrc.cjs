module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'script',
  },
  rules: {
    // Basic rules for static JS files
    'no-console': 'warn',
    'no-unused-vars': 'warn',
    'no-undef': 'error',
    'semi': ['error', 'always'],
  },
  overrides: [
    {
      files: ['**/*.mjs'],
      env: {
        node: true,
        es2021: true,
      },
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
    },
  ],
};
