#!/usr/bin/env bash
# Common Oracle CLI bundles and examples for WorldArchitect.AI.

# Core docs and high-level context.
export WA_DOCS="README.md,CLAUDE.md,CODE_REVIEW_SUMMARY.md"

# Backend core (API, schemas).
export BACKEND="mvp_site/*.py,mvp_site/schemas/**/*.py"

# AI and game-logic hot path.
export AI_CORE="mvp_site/gemini_service.py,mvp_site/gemini_response.py,mvp_site/dual_pass_generator.py,mvp_site/robust_json_parser.py,mvp_site/game_state.py,mvp_site/entity_validator.py,mvp_site/narrative_response_schema.py,mvp_site/world_logic.py"

# MCP/API gateway boundary.
export MCP="mvp_site/main.py,mvp_site/world_logic.py,mvp_site/mcp_api.py,mvp_site/mcp_client.py"

# Frontend bundle (split globs to avoid brace issues).
export FRONTEND="mvp_site/frontend_v1/**/*.js,mvp_site/frontend_v1/**/*.css,mvp_site/frontend_v1/**/*.html"

# Tests (unit + integration).
export TESTS="tests/**/*.py,test_integration/**/*.py"

# Quick architecture review (dry-run preview).
oracle_arch_preview() {
  oracle --dry-run summary \
    -p "Fast architecture review of WorldArchitect.AI; describe components, how MCP/Flask/Gemini/Firestore fit; top 5 cleanup opportunities." \
    --file "README.md,$BACKEND,$FRONTEND"
}

# Architecture review (API run).
oracle_arch() {
  oracle --wait \
    -p "Fast architecture review of WorldArchitect.AI; describe components, how MCP/Flask/Gemini/Firestore fit; top 5 cleanup opportunities." \
    --file "README.md,$BACKEND,$FRONTEND"
}

# Debug AI pipeline with a bug report file (pass path as $1, default tmp/bug-report.md).
oracle_ai_debug() {
  local report="${1:-tmp/bug-report.md}"
  oracle --wait --files-report \
    -p "We have a bug in the AI story pipeline (see bug report). Walk HTTP->MCP->Gemini->JSON parsing->state/validators, pinpoint likely failures, propose a minimal patch and tests." \
    --file "$MCP,$AI_CORE,$TESTS,$report"
}

# Diff review: expects git diff saved to /tmp/wa.patch.
oracle_diff_review() {
  git diff > /tmp/wa.patch
  oracle --wait --write-output wa-review.md \
    -p "Senior review of this diff for WorldArchitect.AI (correctness, perf, security, architecture alignment). Return a short summary and file-grouped comments." \
    --file "$WA_DOCS,/tmp/wa.patch"
}

# Frontend bug triage with optional note file (pass path as $1, default tmp/ui-bug.md).
oracle_ui_debug() {
  local note="${1:-tmp/ui-bug.md}"
  oracle --wait \
    -p "Frontend bug (see note). Find likely causes in campaign wizard and related modules; propose concrete JS/CSS fixes and a minimal regression test." \
    --file "$note,$FRONTEND,testing_ui/**/*.js"
}
