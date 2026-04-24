# /browserclaw

Reverse-engineer browser APIs from an interactive browsing session.

## Usage

```bash
/browserclaw https://www.linkedin.com/feed/
/browserclaw inspect LinkedIn messaging APIs
```

## Behavior

1. Resolve the target URL or site from the argument.
2. Ask whether the user wants manual capture or scripted capture.
3. Run `browserclaw reverse` with an output directory under `generated/<site>/`.
4. Summarize the emitted:
   - `capture.har`
   - `catalog.json`
   - `generated_client.py`
   - `mcp_tools.json`
5. Do not claim auth bypass, CAPTCHA bypass, or stealth support.

## Examples

```bash
browserclaw reverse --url https://www.linkedin.com/feed/ --output-dir generated/linkedin --manual
browserclaw reverse --url https://app.example.com --output-dir generated/example --goal "Open invoices and capture list/detail APIs" --provider anthropic --model claude-sonnet-4-20250514
```

