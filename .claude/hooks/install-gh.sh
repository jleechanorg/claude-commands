#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[install-gh] %s\n' "$1" >&2
}

if command -v gh >/dev/null 2>&1; then
  log "GitHub CLI already available at $(command -v gh)"
  exit 0
fi

OS_NAME=$(uname -s)
case "$OS_NAME" in
  Linux) OS="linux" ;;
  Darwin) OS="macOS" ;;
  *)
    log "Unsupported operating system: $OS_NAME"
    exit 1
    ;;
esac

ARCH_NAME=$(uname -m)
case "$ARCH_NAME" in
  x86_64|amd64) ARCH="amd64" ;;
  arm64|aarch64) ARCH="arm64" ;;
  *)
    log "Unsupported CPU architecture: $ARCH_NAME"
    exit 1
    ;;
esac

DEFAULT_VERSION="2.57.0"
VERSION="${GH_CLI_VERSION:-}"
if [ -z "$VERSION" ]; then
  if command -v curl >/dev/null 2>&1; then
    VERSION=$(curl -fsSL "https://api.github.com/repos/cli/cli/releases/latest" \
      | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'].lstrip('v'))" 2>/dev/null || true)
  fi
  if [ -z "$VERSION" ]; then
    VERSION="$DEFAULT_VERSION"
    log "Falling back to default GitHub CLI version v${VERSION}"
  else
    log "Detected latest GitHub CLI version v${VERSION}"
  fi
else
  log "Using configured GitHub CLI version v${VERSION}"
fi

ARCHIVE="gh_${VERSION}_${OS}_${ARCH}.tar.gz"
URL="https://github.com/cli/cli/releases/download/v${VERSION}/${ARCHIVE}"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

log "Downloading ${URL}"
curl -fsSL "$URL" -o "$TMP_DIR/gh.tar.gz"

EXTRACT_DIR="$TMP_DIR/extracted"
mkdir -p "$EXTRACT_DIR"
tar -xzf "$TMP_DIR/gh.tar.gz" -C "$EXTRACT_DIR"

SOURCE_DIR=$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name "gh_${VERSION}_*" | head -n 1)
if [ -z "$SOURCE_DIR" ]; then
  log "Unable to locate extracted GitHub CLI payload"
  exit 1
fi

INSTALL_ROOT="${HOME}/.cache/gh-cli"
BIN_DIR="$INSTALL_ROOT/bin"
mkdir -p "$BIN_DIR"

install -m 755 "$SOURCE_DIR/bin/gh" "$BIN_DIR/gh"
log "Installed gh to ${BIN_DIR}/gh"

PATH="$BIN_DIR:$PATH"
if ! command -v gh >/dev/null 2>&1; then
  log "GitHub CLI installation succeeded but ${BIN_DIR} is not on PATH"
  exit 1
fi

log "GitHub CLI available at $(command -v gh)"
exit 0
