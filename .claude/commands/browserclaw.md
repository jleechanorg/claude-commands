# /browserclaw

Reverse-engineer browser APIs from an interactive browsing session.

## Usage

```bash
/browserclaw https://www.linkedin.com/feed/
/browserclaw inspect LinkedIn messaging APIs
/browserclaw learn https://example.com --output-dir ./learned
```

## Commands

| Command | Description |
|---------|-------------|
| `learn` | Capture + infer + generate + save SKILL.md (full pipeline, recommended) |
| `reverse` | Capture + infer + generate |
| `capture` | HAR capture only |
| `capture-ws` | WebSocket frame capture |
| `infer` | Parse HAR → Endpoint Catalog |
| `generate` | Generate client code from catalog |
| `generate-ws` | Generate WebSocket replay scripts |

## Behavior

1. Resolve the target URL or site from the argument.
2. Ask whether the user wants manual capture or scripted capture.
3. Run `browserclaw learn` with an output directory under `generated/<site>/`.
4. Summarize the emitted:
   - `capture.har`
   - `catalog.json`
   - `generated_client.py`
   - `mcp_tools.json`
   - `SKILL.md` ← the saved skill for this site
5. Do not claim auth bypass, CAPTCHA bypass, or stealth support.

## Examples

```bash
# Learn a site and save its skill (recommended)
browserclaw learn --url https://www.linkedin.com/feed/ --output-dir generated/linkedin --manual

# With LLM enrichment
browserclaw learn --url https://app.example.com --output-dir generated/example --goal "Open invoices and capture list/detail APIs" --provider anthropic --model claude-sonnet-4-20250514

# Reverse (no skill output)
browserclaw reverse --url https://www.linkedin.com/feed/ --output-dir generated/linkedin --manual

# Generate skill from existing catalog
browserclaw generate --catalog /tmp/catalog.json --output-dir ./out --save-skill
```

