#!/usr/bin/env bash
set -euo pipefail

# Publish orchestration or automation package to PyPI with a single command.
# Usage:
#   scripts/publish_pypi.sh orchestration 0.1.7
#   scripts/publish_pypi.sh automation 0.2.1
# Options:
#   --testpypi   Use TestPyPI instead of PyPI
#   --local-test After upload, pip install the built wheels from dist/
#
# Requirements:
#   - twine, build installed in PATH
#   - PyPI token in ~/.bashrc (export PYPI_TOKEN=...) or ~/.pypirc [pypi] password
#   - Run from repo root

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET=""
VERSION=""
REPO_URL="https://upload.pypi.org/legacy/"
PIP_INDEX="https://pypi.org/simple"
LOCAL_TEST=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    orchestration|automation)
      TARGET="$1"
      VERSION="${2:-}"
      if [[ -z "$VERSION" || "$VERSION" == --* ]]; then
        echo "ERROR: missing or invalid version argument for target '$TARGET'."
        echo "Usage: scripts/publish_pypi.sh [orchestration|automation] <version> [--testpypi] [--local-test]"
        exit 1
      fi
      shift 2
      ;;
    --testpypi)
      REPO_URL="https://test.pypi.org/legacy/"
      PIP_INDEX="https://test.pypi.org/simple"
      shift
      ;;
    --local-test)
      LOCAL_TEST=1
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$TARGET" || -z "$VERSION" ]]; then
  echo "Usage: scripts/publish_pypi.sh [orchestration|automation] <version> [--testpypi] [--local-test]"
  exit 1
fi

case "$TARGET" in
  orchestration)
    PKG_DIR="$REPO_ROOT/orchestration"
    PKG_NAME="jleechanorg-orchestration"
    DEP_BUMP=0
    ORCH_VERSION_TARGET="$VERSION"
    ;;
  automation)
    PKG_DIR="$REPO_ROOT/automation"
    PKG_NAME="jleechanorg-pr-automation"
    DEP_BUMP=1
    ORCH_PYPROJECT="$REPO_ROOT/orchestration/pyproject.toml"
    # Read the current orchestration version from repo to align dependency
    ORCH_VERSION_TARGET="$(
python3 - <<PY
import pathlib
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
path = pathlib.Path("$REPO_ROOT/orchestration/pyproject.toml")
data = tomllib.loads(path.read_text())
print(data["project"]["version"])
PY
)"
    ;;
esac

if ! command -v twine >/dev/null || ! command -v python3 >/dev/null; then
  echo "ERROR: twine and python3 are required on PATH"
  exit 1
fi

PYPI_TOKEN="$(grep -o 'pypi-[A-Za-z0-9._-]*' ~/.bashrc 2>/dev/null | head -n1 || true)"
if [[ -z "$PYPI_TOKEN" && -f "$HOME/.pypirc" ]]; then
  PYPI_TOKEN="$(python3 - <<'PY'
import configparser, os
cfg = configparser.ConfigParser()
cfg.read(os.path.expanduser('~/.pypirc'))
print(cfg.get('pypi', 'password', fallback=''))
PY
)"
fi
if [[ -z "$PYPI_TOKEN" ]]; then
  echo "ERROR: No PyPI token found in ~/.bashrc or ~/.pypirc"
  exit 1
fi

trap 'cd "$REPO_ROOT" 2>/dev/null || true' EXIT

cd "$PKG_DIR"
echo "🔧 Bumping $PKG_NAME to version $VERSION"
python3 - <<PY
import pathlib, sys
try:
    import tomllib
except ModuleNotFoundError:  # py39
    import tomli as tomllib
import tomli_w

path = pathlib.Path("pyproject.toml")
data = tomllib.loads(path.read_text())
data["project"]["version"] = "$VERSION"
# If automation, bump orchestration dep to the repo's orchestration version
if "$DEP_BUMP" == "1":
    deps = data["project"].get("dependencies", [])
    out = []
    found = False
    for d in deps:
        if d.startswith("jleechanorg-orchestration"):
            out.append(f"jleechanorg-orchestration>=$ORCH_VERSION_TARGET")
            found = True
        else:
            out.append(d)
    if not found:
        out.append(f"jleechanorg-orchestration>=$ORCH_VERSION_TARGET")
    data["project"]["dependencies"] = out
path.write_text(tomli_w.dumps(data))
PY

echo "🧹 Cleaning dist/build"
echo "⚠️  Removing dist/ and build/ directories..."
rm -rf dist build

echo "🏗️ Building wheel/sdist"
python3 -m build

echo "🚀 Uploading to $REPO_URL"
TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_TOKEN" \
  python3 -m twine upload --non-interactive --repository-url "$REPO_URL" dist/*

echo "⏳ Waiting for index to reflect upload..."
sleep 10
curl -sL "$PIP_INDEX/$PKG_NAME/" | grep -o "$VERSION" | head -n1 || true

if [[ $LOCAL_TEST -eq 1 ]]; then
  echo "🧪 Local install test from dist/"
  python3 -m pip install --no-cache-dir --upgrade dist/*.whl
fi

echo "✅ Done. Package: $PKG_NAME Version: $VERSION"
