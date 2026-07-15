#!/usr/bin/env bash
set -euo pipefail

BASHRC_PATH="${1:-${BASHRC_PATH:-$HOME/.bashrc}}"
if [[ ! -f "$BASHRC_PATH" ]]; then
  echo "ERROR: Bash RC file not found: $BASHRC_PATH"
  exit 2
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl is required"
  exit 2
fi

source "$BASHRC_PATH"

results=()

record_result() {
  local service="$1"
  local status="$2"
  local details="${3:-}"
  results+=("${service}|${status}|${details}")
}

check_github() {
  local token="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
  if [[ -z "${token}" ]]; then
    record_result "GitHub" "FAIL" "GITHUB_TOKEN/GH_TOKEN not set"
    return
  fi

  local tmp_http tmp_code
  tmp_http="$(mktemp)"
  tmp_code="$(curl --max-time 12 --fail --silent --show-error \
    -H "Authorization: Bearer ${token}" \
    -H "Accept: application/vnd.github+json" \
    -o "$tmp_http" \
    -w "%{http_code}" \
    "https://api.github.com/user" || true)"

  if [[ "$tmp_code" == "200" ]] && grep -q '"login"' "$tmp_http" 2>/dev/null; then
    record_result "GitHub" "PASS" "auth.user endpoint returned 200"
  elif [[ "$tmp_code" == "401" ]]; then
    record_result "GitHub" "FAIL" "invalid/expired token (HTTP 401)"
  elif [[ "$tmp_code" == "200" ]]; then
    record_result "GitHub" "PASS" "HTTP 200 returned"
  elif [[ "$tmp_code" == "403" ]]; then
    record_result "GitHub" "FAIL" "forbidden token scope or secondary rate limit (HTTP 403)"
  else
    record_result "GitHub" "FAIL" "curl failure or unexpected response (HTTP ${tmp_code:-unknown})"
  fi
  rm -f "$tmp_http"
}

check_slack_tokens() {
  local var token
  local got_any=0

  for var in SLACK_MCP_XOXP_TOKEN SLACK_BOT_TOKEN SLACK_MCP_XOXB_TOKEN HERMES_SLACK_BOT_TOKEN; do
    token="${!var-}"
    if [[ -z "$token" ]]; then
      continue
    fi
    got_any=1
    local tmp_http tmp_code
    tmp_http="$(mktemp)"
    tmp_code="$(curl --max-time 12 --silent --show-error \
      -H "Authorization: Bearer ${token}" \
      -o "$tmp_http" \
      -w "%{http_code}" \
      "https://slack.com/api/auth.test" || true)"
    if [[ "$tmp_code" == "200" ]] && grep -q '"ok"[[:space:]]*:[[:space:]]*true' "$tmp_http"; then
      record_result "Slack (${var})" "PASS" "auth.test ok"
    else
      record_result "Slack (${var})" "FAIL" "auth.test failed or non-working token (HTTP ${tmp_code:-unknown})"
    fi
    rm -f "$tmp_http"
  done

  if [[ "$got_any" -eq 0 ]]; then
    record_result "Slack" "FAIL" "no Slack bot/user tokens set"
  fi
}

check_aws() {
  if [[ -z "${AWS_ACCESS_KEY_ID:-}" || -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
    record_result "AWS" "FAIL" "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY not set"
    return
  fi

  if ! command -v aws >/dev/null 2>&1; then
    record_result "AWS" "SKIP" "aws cli missing"
    return
  fi

  local aws_err
  if AWS_PAGER="" aws sts get-caller-identity --output text --query Arn >/tmp/aws_caller.out 2>/tmp/aws_caller.err; then
    aws_out="$(cat /tmp/aws_caller.out 2>/dev/null | tr -d '\n')"
    rm -f /tmp/aws_caller.out /tmp/aws_caller.err
    record_result "AWS" "PASS" "sts get-caller-identity succeeds"
  else
    aws_err="$(cat /tmp/aws_caller.err 2>/dev/null | tr -d '\n' | sed 's/"//g' )"
    rm -f /tmp/aws_caller.out /tmp/aws_caller.err
    record_result "AWS" "FAIL" "sts get-caller-identity failed: ${aws_err:-unknown error}"
  fi
}

check_telegram() {
  if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
    record_result "Telegram" "FAIL" "TELEGRAM_BOT_TOKEN not set"
    return
  fi

  local tmp_http tmp_code
  tmp_http="$(mktemp)"
  tmp_code="$(curl --max-time 12 --silent --show-error \
    -o "$tmp_http" \
    -w "%{http_code}" \
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" || true)"
  if [[ "$tmp_code" == "200" ]] && grep -q '"ok"[[:space:]]*:[[:space:]]*true' "$tmp_http"; then
    record_result "Telegram" "PASS" "getMe ok"
  else
    record_result "Telegram" "FAIL" "getMe failed (HTTP ${tmp_code:-unknown})"
  fi
  rm -f "$tmp_http"
}

check_google_service_account_file() {
  local key_path="${GOOGLE_APPLICATION_CREDENTIALS:-${WORLDARCH_SERVICE_ACCOUNT_KEY:-}}"
  if [[ -z "$key_path" ]]; then
    record_result "Google SA file" "FAIL" "GOOGLE_APPLICATION_CREDENTIALS/WORLDARCH_SERVICE_ACCOUNT_KEY not set"
    return
  fi
  if [[ ! -f "$key_path" ]]; then
    record_result "Google SA file" "FAIL" "file not found: $key_path"
    return
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    record_result "Google SA file" "SKIP" "python3 missing"
    return
  fi
  local gsa_email gsa_err
  if gsa_email="$(python3 -c 'import json,sys; data=json.load(open(sys.argv[1], "r", encoding="utf-8")); print(data.get("client_email",""))' "$key_path" 2>/tmp/gsa_check.err)"; then
    rm -f /tmp/gsa_check.out /tmp/gsa_check.err
    record_result "Google SA file" "PASS" "parsed client_email: ${gsa_email:-(empty)}"
  else
    gsa_err="$(cat /tmp/gsa_check.err 2>/dev/null | head -n 1 | tr -d '\n')"
    rm -f /tmp/gsa_check.out /tmp/gsa_check.err
    record_result "Google SA file" "FAIL" "invalid JSON in service account file (${gsa_err:-unknown})"
  fi
}

check_pypi() {
  if [[ -z "${PYPI_TOKEN:-}" ]]; then
    record_result "PyPI" "FAIL" "PYPI_TOKEN not set"
    return
  fi
  if [[ ! "$PYPI_TOKEN" =~ ^pypi- ]]; then
    record_result "PyPI" "FAIL" "token format does not match pypi- prefix"
    return
  fi
  record_result "PyPI" "PASS" "token format looks valid (pypi- prefix)"
}

check_github
check_slack_tokens
check_telegram
check_google_service_account_file
check_pypi

pass_count=0
fail_count=0
skip_count=0

for item in "${results[@]}"; do
  IFS='|' read -r service status details <<< "$item"
  [[ "$status" == "PASS" ]] && pass_count=$((pass_count + 1))
  [[ "$status" == "FAIL" ]] && fail_count=$((fail_count + 1))
  [[ "$status" == "SKIP" ]] && skip_count=$((skip_count + 1))
  printf "%-28s %-5s %s\n" "$service" "$status" "$details"
done

echo
echo "Summary: PASS=$pass_count FAIL=$fail_count SKIP=$skip_count"

if [[ "$fail_count" -gt 0 ]]; then
  exit 1
fi
