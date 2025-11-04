---
description: Get multi-model second opinion on design, code review, or bugs
aliases: [secondopinion]
type: ai
execution_mode: immediate
---

# Second Opinion Command

Get comprehensive multi-model AI feedback on your code, design decisions, or bug analysis.

**🚀 Uses command-line approach to bypass 25K token limits and send full PR context!**

## Usage

```bash
# Get second opinion on current PR branch
/secondo

# Specify feedback type
/secondo design
/secondo code-review
/secondo bugs

# With specific question
/secondo "Should I use Redis or in-memory caching for rate limiting?"
```

## How It Works

This command uses a direct approach with auth-cli.mjs for secure token management:

1. **Authentication** (Auto-Refresh):
   - Uses `~/.claude/scripts/auth-cli.mjs token` for secure token retrieval
   - Automatically refreshes expired ID tokens using refresh token (silent, no browser popup)
   - ID tokens expire after 1 hour, refresh tokens enable 30+ day sessions
   - Only opens browser for initial login or if refresh token expires

2. **Gather Full PR Context**:
   - Current branch vs main git diff
   - All changed file contents
   - Recent commit messages
   - Critical code sections

3. **Build Comprehensive Request**:
   - Create detailed analysis request (optimized to stay under 25K tokens)
   - Include all relevant code context
   - Add production context and testing requirements

4. **Direct MCP Server Call**:
   - Uses HTTPie with auto-refreshed Bearer token
   - Sends to: `https://ai-universe-backend-dev-114133832173.us-central1.run.app/mcp`
   - Handles streaming responses properly
   - Saves results locally

5. **Multi-Model Analysis**:
   - Gemini (Primary model)
   - Perplexity (Secondary)
   - OpenAI (Secondary)
   - Synthesis with 50+ authoritative sources

6. **Results Display**:
   - Save comprehensive report to `tmp/secondo_analysis_[timestamp].md`
   - Display verdict and key findings
   - Show token usage and cost breakdown

## Implementation Protocol

When executing `/second_opinion` or `/secondo`:

### Step 0: Authentication Setup (Auto-Refresh)
```bash
# Verify auth-cli.mjs is installed
if [ ! -f "$HOME/.claude/scripts/auth-cli.mjs" ]; then
  echo "❌ auth-cli.mjs not found. Run /localexportcommands to install"
  exit 1
fi

# Get token (auto-refreshes if expired using refresh token)
# This is silent - only prompts for login if refresh token is invalid/missing
TOKEN=$(node ~/.claude/scripts/auth-cli.mjs token)

# If this fails, user needs to authenticate
if [ $? -ne 0 ]; then
  echo "❌ Authentication failed. Please run:"
  echo "   node ~/.claude/scripts/auth-cli.mjs login"
  exit 1
fi
```

**Key Behavior**:
- **Seamless Auto-Refresh**: Automatically renews ID tokens using refresh token (no browser popup)
- **30+ Day Sessions**: Refresh tokens enable long-lived sessions without re-authentication
- **Browser Only When Needed**: Only opens browser for initial login or if refresh token expires
- **Same Token File**: Uses `~/.ai-universe/auth-token.json` (exact same as AI Universe repo)

### Step 1: Gather PR Context
```bash
# Get current branch name
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Get git diff stats
git diff origin/main...HEAD --stat > /tmp/secondo_diff_stats.txt

# Get full git diff
git diff origin/main...HEAD > /tmp/secondo_diff_full.txt

# Get recent commits
git log origin/main..HEAD --oneline --no-decorate > /tmp/secondo_commits.txt

# Get changed files list
git diff origin/main...HEAD --name-only > /tmp/secondo_files.txt
```

### Step 2: Build Analysis Request

Create `/tmp/secondo_request.json` with this structure:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "agent_second_opinion",
    "arguments": {
      "question": "[Comprehensive question with full PR context - see template below]",
      "primaryModel": "gemini",
      "secondaryModels": ["perplexity", "openai"],
      "maxOpinions": 3
    }
  },
  "id": 1
}
```

**Question Template** (optimize to ~500 words for maximum code context):
```
# PR Analysis Request

**Branch**: [branch_name]
**Base**: main
**Changes**: [X files, +Y/-Z lines]

## Critical Changes

[Include git diff --stat output]

## Key Code Sections

[Include critical changed sections from main files]

## Commits

[Include commit messages]

## Production Context

This is production code for [project description].

## Question

Analyze this PR for serious correctness bugs, security issues, and production safety concerns. Focus on:
1. Logic errors and edge cases
2. Security vulnerabilities
3. Production safety (error handling, resource management)
4. Data integrity issues

Do NOT provide style or documentation feedback. Only report bugs that could cause failures, data loss, or security issues in production.
```

### Step 3: Execute Request

```bash
# Call MCP server directly with curl
curl -X POST "https://ai-universe-backend-dev-114133832173.us-central1.run.app/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  --data-binary @/tmp/secondo_request.json \
  --silent \
  --max-time 180 \
  -o /tmp/secondo_response.json

# Check if successful
if [ $? -eq 0 ] && [ -s /tmp/secondo_response.json ]; then
  echo "✅ Analysis complete"
else
  echo "❌ Request failed"
  exit 1
fi
```

### Step 4: Parse and Display Results

Extract from `/tmp/secondo_response.json`:
1. Parse the JSON response (look for `result.content[0].text`)
2. Extract verdict, token counts, costs, sources
3. Save formatted report to `tmp/secondo_analysis_[timestamp].md`
4. Display key findings to user

**Example parsing**:
```bash
# Extract the main response text
jq -r '.result.content[0].text' /tmp/secondo_response.json > /tmp/secondo_parsed.txt

# Extract metrics if available
TOKENS=$(jq -r '.result.content[0].text' /tmp/secondo_response.json | grep -o 'Total Tokens: [0-9,]*' | head -1)
COST=$(jq -r '.result.content[0].text' /tmp/secondo_response.json | grep -o 'Total Cost: \$[0-9.]*' | head -1)
```

## Token Optimization

**Maximum token budget**: 24,900 tokens (stay under 25K limit)

**Allocation strategy**:
- **Request overhead**: ~100 tokens (JSON structure)
- **Question/context**: ~500-1000 words (optimize for clarity)
- **Git diff stats**: Full output (~100-500 tokens)
- **Critical code sections**: ~15K tokens (selective, not full files)
- **Commit messages**: ~200 tokens
- **Metadata**: ~100 tokens

**Tips to maximize context**:
1. Include git diff --stat (compact, informative)
2. Select critical changed sections (not full files)
3. Prioritize files with complex logic changes
4. Keep question focused (~500 words)
5. Skip unchanged context

## Authentication & Rate Limits

**Authentication**: Required via Firebase OAuth (exact same as AI Universe repo)
- **Initial Login**: `node ~/.claude/scripts/auth-cli.mjs login` (browser-based OAuth, run outside Claude Code)
- **Check Status**: `node ~/.claude/scripts/auth-cli.mjs status` (view current auth status)
- **Token Location**: `~/.ai-universe/auth-token.json` (ID token + refresh token)
- **Session Duration**: 30+ days (refresh tokens auto-renew ID tokens silently)
- **Auto-Refresh**: `/secondo` automatically refreshes expired ID tokens (no browser popup needed)

**Token Lifecycle**:
- **ID Token**: Expires after 1 hour (Firebase security policy)
- **Refresh Token**: Enables automatic ID token renewal for 30+ days
- **Auto-Renewal**: Silent, seamless - only opens browser if refresh token expires

**When You'll Need to Re-authenticate**:
- Initial setup (no token file exists)
- After 30+ days (when refresh token expires)
- If token file is corrupted or manually deleted

**Rate Limits**: Applied per authenticated user based on Firebase account

**Practical limits**:
- Server timeout: 180 seconds max
- Token limit: 25,000 tokens per response
- Cost: ~$0.10 per full PR analysis (3 models)

## Output Format

Display results in markdown with:
- 📊 **Summary**: Models used, tokens, cost, sources
- 🎯 **Verdict**: Unanimous consensus or majority opinion
- ⚠️ **Critical Issues**: Security, correctness, production safety
- 💡 **Model Perspectives**: Individual model insights
- ✅ **Validation**: What was confirmed as correct
- 🔗 **Sources**: Authoritative references (50+)

**Save to**: `tmp/secondo_analysis_[timestamp].md`

## Success Criteria

✅ Request completes successfully (curl exit code 0)
✅ Response file is non-empty
✅ Response contains valid JSON with `result.content`
✅ Analysis report saved to tmp directory
✅ User sees verdict and key findings

## Error Handling

**Common issues**:
1. **Token limit exceeded**: Reduce code context, keep question focused
2. **Timeout**: Complex analysis may take 60-120 seconds, use `--max-time 180`
3. **Empty response**: Check curl exit code, verify network connectivity
4. **JSON parse error**: Response may be streaming format, extract text content first

## Example Execution Flow

```
User: /secondo

1. Gather PR context:
   ✓ Branch: fix_mcp
   ✓ Changed files: 18 files (+2448/-799)
   ✓ Git diff saved to /tmp/secondo_diff_full.txt
   ✓ Commits: 5 commits analyzed

2. Build analysis request:
   ✓ Question: 487 words
   ✓ Code context: 14,250 tokens
   ✓ Total estimated: 23,890 tokens (95.6% of limit)

3. Execute request:
   ✓ curl -X POST [MCP endpoint]
   ✓ Response: 73KB received in 47 seconds
   ✓ Status: HTTP 200 OK

4. Parse results:
   ✓ Models: 3 (Gemini, Perplexity, OpenAI)
   ✓ Total tokens: 24,964
   ✓ Total cost: $0.10193
   ✓ Sources: 52 authoritative references

5. Display verdict:
   🎯 UNANIMOUS VERDICT: CORRECT (with caveats)

   ✅ Fix is safe for production
   ⚠️ Array initialization discipline required
   📊 Report saved: tmp/secondo_analysis_20251031_1847.md
```
