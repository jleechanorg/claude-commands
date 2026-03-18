#!/usr/bin/env bash
set -euo pipefail

# Stop hook input is provided as JSON on stdin.
payload="$(cat)"
cwd=""
model=""
ctx_pct=""
tok_in=""
tok_out=""
tok_total=""
cost_usd=""
burn_rate_usd_hr=""
elapsed_seconds=""
reset_seconds=""

if command -v jq >/dev/null 2>&1; then
  cwd="$(printf '%s' "$payload" | jq -r '.cwd // ""' 2>/dev/null || true)"
  model="$(printf '%s' "$payload" | jq -r '
    .model.display_name //
    .model.name //
    .model.id //
    .model //
    .agent.model.display_name //
    .agent.model.name //
    .agent.model.id //
    .agent.model //
    empty
  ' 2>/dev/null || true)"
  ctx_pct="$(printf '%s' "$payload" | jq -r '
    .context_window.used_percentage //
    .context.used_percentage //
    .usage.context_window_percent //
    .usage.context_percent //
    empty
  ' 2>/dev/null || true)"
  tok_in="$(printf '%s' "$payload" | jq -r '
    .usage.input_tokens //
    .usage.prompt_tokens //
    .token_usage.input_tokens //
    .tokens.input //
    empty
  ' 2>/dev/null || true)"
  tok_out="$(printf '%s' "$payload" | jq -r '
    .usage.output_tokens //
    .usage.completion_tokens //
    .token_usage.output_tokens //
    .tokens.output //
    empty
  ' 2>/dev/null || true)"
  tok_total="$(printf '%s' "$payload" | jq -r '
    .usage.total_tokens //
    .token_usage.total_tokens //
    .tokens.total //
    empty
  ' 2>/dev/null || true)"
  cost_usd="$(printf '%s' "$payload" | jq -r '
    .usage.cost_usd //
    .cost.usd //
    .session.cost_usd //
    empty
  ' 2>/dev/null || true)"
  burn_rate_usd_hr="$(printf '%s' "$payload" | jq -r '
    .usage.burn_rate_usd_per_hour //
    .cost.burn_rate_usd_per_hour //
    .session.burn_rate_usd_per_hour //
    empty
  ' 2>/dev/null || true)"
  elapsed_seconds="$(printf '%s' "$payload" | jq -r '
    .session.elapsed_seconds //
    .elapsed_seconds //
    ((.session.elapsed_ms // .elapsed_ms) / 1000 | floor) //
    empty
  ' 2>/dev/null || true)"
  reset_seconds="$(printf '%s' "$payload" | jq -r '
    .rate_limits.block_reset_seconds //
    .rate_limits.reset_seconds //
    .block_reset_seconds //
    .reset_seconds //
    empty
  ' 2>/dev/null || true)"
fi

status_line=""
pr_url=""
if [ -n "$cwd" ] && [ -d "$cwd" ]; then
  if [ -x "$cwd/.claude/hooks/git-header.sh" ]; then
    header_output="$(cd "$cwd" && COLUMNS=500 "$cwd/.claude/hooks/git-header.sh" --status-only 2>/dev/null || true)"
    status_line="$(printf '%s\n' "$header_output" | sed -n '1p')"
    pr_url="$(printf '%s\n' "$header_output" | grep -E '^https?://' | head -n 1 || true)"
  elif [ -x "$cwd/.codex/hooks/git-header.sh" ]; then
    header_output="$(cd "$cwd" && COLUMNS=500 "$cwd/.codex/hooks/git-header.sh" 2>/dev/null || true)"
    status_line="$(printf '%s\n' "$header_output" | sed -n '1p')"
    pr_url="$(printf '%s\n' "$header_output" | grep -E '^https?://' | head -n 1 || true)"
  elif [ -x "$HOME/.claude/hooks/git-header.sh" ]; then
    header_output="$(cd "$cwd" && COLUMNS=500 "$HOME/.claude/hooks/git-header.sh" --status-only 2>/dev/null || true)"
    status_line="$(printf '%s\n' "$header_output" | sed -n '1p')"
    pr_url="$(printf '%s\n' "$header_output" | grep -E '^https?://' | head -n 1 || true)"
  elif [ -x "$HOME/.codex/hooks/git-header.sh" ]; then
    header_output="$(cd "$cwd" && COLUMNS=500 "$HOME/.codex/hooks/git-header.sh" 2>/dev/null || true)"
    status_line="$(printf '%s\n' "$header_output" | sed -n '1p')"
    pr_url="$(printf '%s\n' "$header_output" | grep -E '^https?://' | head -n 1 || true)"
  fi
fi

clean_num() {
  local v="${1:-}"
  if [ -z "$v" ] || [ "$v" = "null" ]; then
    printf ''
    return
  fi
  # Keep only number-like values; strip whitespace.
  v="$(printf '%s' "$v" | tr -d '[:space:]')"
  if printf '%s' "$v" | grep -Eq '^-?[0-9]+([.][0-9]+)?$'; then
    printf '%s' "$v"
  else
    printf ''
  fi
}

format_int() {
  local v
  v="$(clean_num "$1")"
  if [ -z "$v" ]; then
    return
  fi
  printf '%.0f' "$v" 2>/dev/null || true
}

format_money() {
  local v
  v="$(clean_num "$1")"
  if [ -z "$v" ]; then
    return
  fi
  printf '$%.4g' "$v" 2>/dev/null || true
}

format_duration() {
  local raw
  raw="$(format_int "$1")"
  if [ -z "$raw" ]; then
    return
  fi
  local h=$((raw / 3600))
  local m=$(((raw % 3600) / 60))
  local s=$((raw % 60))
  if [ "$h" -gt 0 ]; then
    printf '%dh%02dm' "$h" "$m"
  elif [ "$m" -gt 0 ]; then
    printf '%dm%02ds' "$m" "$s"
  else
    printf '%ds' "$s"
  fi
}

ctx_int="$(format_int "$ctx_pct")"
ctx_segment=""
if [ -n "$ctx_int" ]; then
  if [ "$ctx_int" -lt 0 ]; then
    ctx_int=0
  fi
  if [ "$ctx_int" -gt 100 ]; then
    ctx_int=100
  fi
  filled=$((ctx_int / 10))
  empty=$((10 - filled))
  bar=""
  if [ "$filled" -gt 0 ]; then
    bar="$(printf "%${filled}s" | tr ' ' '■')"
  fi
  if [ "$empty" -gt 0 ]; then
    bar="${bar}$(printf "%${empty}s" | tr ' ' '□')"
  fi
  ctx_segment="Ctx:[${bar}] ${ctx_int}%"
fi

tok_in_i="$(format_int "$tok_in")"
tok_out_i="$(format_int "$tok_out")"
tok_total_i="$(format_int "$tok_total")"
if [ -z "$tok_total_i" ] && [ -n "$tok_in_i" ] && [ -n "$tok_out_i" ]; then
  tok_total_i=$((tok_in_i + tok_out_i))
fi

token_segment=""
if [ -n "$tok_in_i" ] || [ -n "$tok_out_i" ] || [ -n "$tok_total_i" ]; then
  token_segment="Tok"
  [ -n "$tok_in_i" ] && token_segment="${token_segment} I:${tok_in_i}"
  [ -n "$tok_out_i" ] && token_segment="${token_segment} O:${tok_out_i}"
  [ -n "$tok_total_i" ] && token_segment="${token_segment} T:${tok_total_i}"
fi

cost_segment=""
cost_fmt="$(format_money "$cost_usd")"
burn_fmt="$(format_money "$burn_rate_usd_hr")"
if [ -n "$cost_fmt" ] || [ -n "$burn_fmt" ]; then
  if [ -n "$cost_fmt" ] && [ -n "$burn_fmt" ]; then
    cost_segment="Cost:${cost_fmt} ${burn_fmt}/hr"
  elif [ -n "$cost_fmt" ]; then
    cost_segment="Cost:${cost_fmt}"
  else
    cost_segment="Burn:${burn_fmt}/hr"
  fi
fi

timer_segment=""
elapsed_fmt="$(format_duration "$elapsed_seconds")"
reset_fmt="$(format_duration "$reset_seconds")"
if [ -n "$elapsed_fmt" ] || [ -n "$reset_fmt" ]; then
  if [ -n "$elapsed_fmt" ] && [ -n "$reset_fmt" ]; then
    timer_segment="Time:${elapsed_fmt} Reset:${reset_fmt}"
  elif [ -n "$elapsed_fmt" ]; then
    timer_segment="Time:${elapsed_fmt}"
  else
    timer_segment="Reset:${reset_fmt}"
  fi
fi

model_segment=""
if [ -n "$model" ] && [ "$model" != "null" ]; then
  model_segment="Model:${model}"
fi

pr_segment=""
if [ -n "$pr_url" ]; then
  pr_segment="PR:${pr_url}"
fi

extra=""
append_segment() {
  local part="$1"
  if [ -n "$part" ]; then
    if [ -n "$extra" ]; then
      extra="${extra} | ${part}"
    else
      extra="${part}"
    fi
  fi
}

append_segment "$model_segment"
append_segment "$pr_segment"
append_segment "$ctx_segment"
append_segment "$token_segment"
append_segment "$cost_segment"
append_segment "$timer_segment"

if [ -n "$extra" ]; then
  if [ -n "$status_line" ]; then
    status_line="${status_line} | ${extra}"
  else
    status_line="$extra"
  fi
fi

# Hooks engine expects JSON on stdout.
if command -v jq >/dev/null 2>&1; then
  if [ -n "$status_line" ]; then
    jq -cn --arg msg "$status_line" '{continue:true, systemMessage:$msg}'
  else
    jq -cn '{continue:true}'
  fi
else
  if [ -n "$status_line" ]; then
    escaped=$(printf '%s' "$status_line" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\r/\\r/g' | tr -d '\n')
    printf '{"continue":true,"systemMessage":"%s"}\n' "$escaped"
  else
    printf '{"continue":true}\n'
  fi
fi
