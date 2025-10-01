# Task: Create Simple TypeScript MCP Server

**Working Directory**: You are in `/Users/jleechan/projects_other/worldai_ralph2`

## IMMEDIATE TASK: Create a basic TypeScript MCP server with ONE tool

### Step 1: Initialize TypeScript (iteration 1-2)
```bash
npm init -y
npm install --save-dev typescript @types/node ts-node
npm install @modelcontextprotocol/sdk
npx tsc --init
```

### Step 2: Create server.ts (iteration 3-5)
Create `src/server.ts` with a simple MCP server that has ONE tool: `create_campaign`

```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const server = new Server(
  {
    name: 'worldarchitect-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'create_campaign',
        description: 'Create a new D&D campaign',
        inputSchema: {
          type: 'object',
          properties: {
            title: { type: 'string' },
            setting: { type: 'string' },
          },
          required: ['title', 'setting'],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'create_campaign') {
    return {
      content: [
        {
          type: 'text',
          text: `Created campaign: ${request.params.arguments?.title}`,
        },
      ],
    };
  }
  throw new Error('Tool not found');
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main();
```

### Step 3: Add package.json scripts (iteration 6)
```json
{
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js"
  }
}
```

### Step 4: Build and test (iteration 7-8)
```bash
npm run build
# Should create dist/server.js
ls -la dist/
```

### Step 5: Commit (iteration 9)
```bash
git add .
git commit -m "feat: basic TypeScript MCP server with create_campaign tool"
```

## SUCCESS CRITERIA
- `src/server.ts` exists
- `dist/server.js` exists (compiled)
- `npm run build` succeeds
- Git commit created
- MARK TASK COMPLETE when all files exist

## STOP CONDITIONS
- If you created `src/server.ts` AND `dist/server.js` AND made a commit → DONE
- Do NOT spend iterations on planning or documentation
- Do NOT create multiple files beyond what's specified
- FOCUS: Get the TypeScript server working, nothing else
