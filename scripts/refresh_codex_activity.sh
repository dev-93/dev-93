#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PATH="/Users/taenam/.nvm/versions/node/v22.17.1/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Leave the checkout untouched if another change or Git operation is in progress.
[[ "$(git branch --show-current)" == "main" ]] || exit 0
[[ -z "$(git status --porcelain)" ]] || exit 0
git fetch --quiet origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || exit 0

python3 scripts/update_ai_activity.py
python3 scripts/update_codex_activity.py
git diff --quiet -- assets/codex-activity.svg assets/ai-usage-dark.svg assets/ai-usage-light.svg && exit 0
git add -- assets/codex-activity.svg assets/ai-usage-dark.svg assets/ai-usage-light.svg
git commit --quiet --only -m "Update AI activity" -- assets/codex-activity.svg assets/ai-usage-dark.svg assets/ai-usage-light.svg
git push --quiet origin main
