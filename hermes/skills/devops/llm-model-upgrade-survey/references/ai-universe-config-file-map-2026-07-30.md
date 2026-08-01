# AI-Universe (jleechanorg/ai_universe) — config file map (2026-07-30)

The three canonical files that control provider/model wiring in the `jleechanorg/ai_universe` monorepo. Touch ALL THREE in any upgrade PR — partial changes leave the cost tracker or display layer out of sync.

## 1. `shared-libs/packages/config-utils/src/ConfigManager.ts`

**Holds**: Default model string per provider, env-var names, context-window limits, endpoint URLs, web-search plugin config.

**Key structures**:

```typescript
const PROVIDER_CONTEXT_TOKEN_LIMITS = Object.freeze({
  cerebras: 262_144,
  claude: 200_000,
  gemini: 1_048_576,
  grok: 1_000_000,
  perplexity: 200_000,
  openai: 128_000
} as const);
```

```typescript
interface AppConfig {
  apiKeys: {
    cerebras: string; openrouter: string; claude: string;
    gemini: string; grok: string; perplexity: string; openai: string;
  };
  models: {
    cerebras: { model: string; maxInputTokens: number; maxOutputTokens: number; endpoint: string; webSearch: {...}; openrouter: {...} };
    claude:   { model: string; maxInputTokens: number; maxOutputTokens: number; };
    gemini:   { model: string; maxInputTokens: number; maxOutputTokens: number; webSearch: { googleSearchRetrieval: {...} }; };
    grok:     { model: string; maxInputTokens: number; maxOutputTokens: number; endpoint: string; searchParameters: {...} };
    perplexity: { model: string; maxInputTokens: number; maxOutputTokens: number; endpoint: string; webSearch: {...} };
    openai:   { model: string; maxInputTokens: number; maxTokens: number; endpoint: string; webSearch: {...} };
  };
}
```

**Default model strings (as of 2026-07-30)**:
- cerebras: `qwen-3-235b-a22b-instruct-2507` (direct Cerebras API)
- cerebras.openrouter fallback: `openai/gpt-oss-120b`
- claude: `claude-sonnet-4-20250514`
- gemini: `gemini-3-flash-preview` (already moved off 2.5 Flash)
- grok: `grok-4-fast`
- perplexity: `sonar-pro`
- openai: `gpt-5-nano`

**Env-var names** (the wrapper class fetches these on `loadConfig()`):
- `CEREBRAS_API_KEY`, `OPENROUTER_API_KEY`, `CLAUDE_API_KEY`, `GEMINI_API_KEY`, `GROK_API_KEY`, `PERPLEXITY_API_KEY`, `OPENAI_API_KEY`

**GCP Secret Manager mapping** (in `getSecretName()`):
```typescript
const mapping: Record<string, string> = {
  'CLAUDE_API_KEY': 'claude-api-key',
  'OPENROUTER_API_KEY': 'openrouter-api-key',
  'GEMINI_API_KEY': 'gemini-api-key',
  'GROK_API_KEY': 'grok-api-key',
  'PERPLEXITY_API_KEY': 'perplexity-api-key',
  'OPENAI_API_KEY': 'openai-api-key'
};
```

## 2. `shared-libs/packages/mcp-server-utils/src/CostCalculator.ts`

**Holds**: Per-1M-token pricing lookup (`PRICING` constant), model-name normalization (`normalizeModelName` + `modelMappings`), synthesis cost rules.

**Key structures**:

```typescript
private static readonly PRICING = {
  'claude-sonnet-4':   { input: 3.00,  output: 15.00 },
  'anthropic-claude':   { input: 3.00,  output: 15.00 },
  'gemini':             { input: 0.50,  output: 3.00  },  // current "gemini" key — uses 3-Flash preview list
  'gemini-2.5-flash':   { input: 0.075, output: 0.30  },  // LEGACY — dead code, no default routes here
  'cerebras':           { input: 0.60,  output: 0.60  },
  'grok-4-fast':        { input: 0.20,  output: 0.50  },
  'grok-3':             { input: 5.00,  output: 15.00 },
  'sonar':              { input: 1.00,  output: 1.00  },
  'sonar-pro':          { input: 3.00,  output: 15.00 },
  'sonar-reasoning':    { input: 1.00,  output: 5.00  },
  'openai-gpt-4o':      { input: 5.00,  output: 15.00 },
  'openai-gpt-5':       { input: 1.25,  output: 10.00 },
  'openai-gpt-5-mini':  { input: 0.25,  output: 2.00  },
  'openai-gpt-5-nano':  { input: 0.05,  output: 0.40  }
};
```

**`modelMappings` (the canonical alias → pricing-key table)** — this is the table you edit when adding a new model id. New models MUST be added in BOTH `PRICING` AND `modelMappings`, otherwise `normalizeModelName` returns the raw model id and the cost lookup falls back to the unknown-model warning.

```typescript
const modelMappings: Record<string, string> = {
  'claude':              'claude-sonnet-4',
  'claude-primary':      'claude-sonnet-4',
  'claude-secondary':    'claude-sonnet-4',
  'grok':                'grok-4-fast',
  'grok-4-fast':         'grok-4-fast',
  'grok-3':              'grok-3',
  'gemini-2.5-flash':    'gemini-2.5-flash',  // legacy
  'gemini-3-flash-preview': 'gemini',          // current default
  'gemini-3.6-flash':    'gemini',            // ← add when upgrading
  'cerebras-primary':    'cerebras',
  'cerebras-secondary':  'cerebras',
  'cerebras - qwen 3 thinking': 'cerebras',
  'openai':              'openai-gpt-5-nano', // default OpenAI
  'gpt-5':               'openai-gpt-5',
  'gpt-5-mini':          'openai-gpt-5-mini',
  'gpt-5-nano':          'openai-gpt-5-nano'
};
```

**Trap**: `modelMappings` normalizes spaced and dashed variants. The candidate generation does:
```typescript
const normalized = model.toLowerCase().trim();
const normalizedWhitespaceCollapsed = normalized.replace(/\s+/g, ' ');
const normalizedDashed = normalizedWhitespaceCollapsed.replace(/_/g, '-');
const normalizedHyphenTight = normalizedDashed.replace(/\s*-\s*/g, '-');
const normalizedSpaceless = normalizedDashed.replace(/\s+/g, '');
```
So `'Gemini 3.6 Flash'`, `'gemini-3.6-flash'`, `'gemini-3-6-flash'`, `'gemini 3 6 flash'` all normalize to the same key. Add the canonical dashed form only.

## 3. `shared-libs/packages/mcp-server-utils/src/ModelDisplayNames.ts`

**Holds**: Map of internal model id → user-facing display name.

```typescript
export const MODEL_DISPLAY_NAMES: Readonly<Record<string, string>> = Object.freeze({
  'cerebras': 'Cerebras - Qwen 3 Thinking',
  'cerebras-primary': 'Cerebras - Qwen 3 Thinking',
  'claude': 'Claude',
  'claude-primary': 'Claude',
  'gemini': 'Gemini',
  'gemini-2.5-flash': 'Gemini 2.5 Flash',
  'gemini-3-flash-preview': 'Gemini 3 Flash',
  'gemini-3.6-flash': 'Gemini 3.6 Flash',  // ← add when upgrading
  'perplexity': 'Perplexity Sonar',
  'grok': 'Grok 4 Fast',
  'grok-3': 'Grok 3',
  'openai': 'OpenAI GPT-5 Nano',
  'gpt-4o': 'OpenAI GPT-4o',
  'gpt-5': 'OpenAI GPT-5',
  'gpt-5-nano': 'OpenAI GPT-5 Nano',
  'multi-model-synthesis': 'Multi-Model Synthesis',
  'step2-final-synthesis': 'Multi-Model Synthesis',
  'step1-primary': 'Primary Model'
});
```

## Frontend fixtures (also touch when upgrading)

The frontend mocks use the old model id in fixtures. Update these too or the unit tests will fail:

- `ai_universe_frontend/src/mocks/mockMcpServer.ts` → `secondaryOpinions[].model: 'gemini'` (bare — doesn't need updating)
- `ai_universe_frontend/src/mockData/canonicalSamples.ts` → `modelId: "gemini-2.0-flash-exp"` (UPDATED for `gemini-3.6-flash`)
- `ai_universe_frontend/src/test/mocks/mcpFixtures.ts` → `modelId: "gemini-2.0-flash-exp"` (UPDATED for `gemini-3.6-flash`)
- `ai_universe_frontend/src/services/__tests__/mcpClient.test.ts` → uses bare `model: 'gemini'` and `modelDisplayName: 'Gemini'` (no change needed)
- `ai_universe_frontend/tests/ConversationTranscript.test.tsx` → `model: 'gemini-1.5'` (legacy, may be fine)

## Tests to run

```bash
cd shared-libs/packages/mcp-server-utils
npm test
```

The `CostCalculator.test.ts` suite verifies every model in `modelMappings` resolves to a pricing key (no fallback warnings). If the new model is missing from `modelMappings`, the test surfaces the warning.

## Sample fixture files (canonical doc schema)

- `ai_universe/docs/backend/schema/examples/agent-second-opinion.sample.json` — the canonical schema for the second-opinion output. `secondaryOpinions[].model` and `modelId` fields must match the new model id.
- `shared-libs/packages/mcp-server-utils/dist/CostCalculator.js` + `ModelDisplayNames.js` — the compiled `.js` artifacts. These are regenerated by `npm run build` in CI; do NOT edit by hand. The PR diff should NOT touch these files.
