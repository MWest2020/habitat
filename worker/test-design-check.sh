#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Tests for the designer role (change add-designer-role), without the image:
# design-check's gates on fixture deliveries, and the role's config files.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
python3 -W error::ResourceWarning "$HERE/design/test_check.py"
for f in "$HERE/settings/designer.json" "$HERE/schemas/designer.json"; do
  jq -e . "$f" >/dev/null || { echo "FAIL invalid JSON: $f"; exit 1; }
done
jq -e '.permissions.deny | index("WebFetch") and index("Bash(curl *)") and index("Bash(git push *)")' \
  "$HERE/settings/designer.json" >/dev/null || { echo "FAIL designer settings: network/push not denied"; exit 1; }
jq -e '.hooks.Stop[0].hooks[0].command == "/opt/habitat/hooks/stop-design-check.sh"' \
  "$HERE/settings/designer.json" >/dev/null || { echo "FAIL designer settings: no Stop gate"; exit 1; }
rc=0; bash "$HERE/../dispatch/designer.sh" >/dev/null 2>&1 || rc=$?
[ "$rc" = 64 ] || { echo "FAIL designer.sh without arguments: exit $rc, want 64"; exit 1; }
echo "ok   designer role config"

# designer_gate: a fake design-check on PATH, a throwaway repo.
# shellcheck source=design-gate.sh
. "$HERE/design-gate.sh"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/repo"
printf '#!/bin/sh\nexit "${FAKE_CHECK_RC:-0}"\n' > "$T/bin/design-check"; chmod +x "$T/bin/design-check"
export PATH="$T/bin:$PATH"
cd "$T/repo" && git init -q && git -c user.name=t -c user.email=t@t commit -q --allow-empty -m base
base=$(git rev-parse HEAD)
mkdir -p design/brand && echo x > design/brand/rationale.md
designer_gate "$base" 2>/dev/null || { echo "FAIL gate: delivery only, check passes"; exit 1; }
FAKE_CHECK_RC=1 designer_gate "$base" 2>/dev/null && { echo "FAIL gate: failing design-check passed"; exit 1; }
mkdir -p web && echo y > web/index.html
designer_gate "$base" 2>/dev/null && { echo "FAIL gate: change outside design/brand passed"; exit 1; }
rm -rf web && echo z > README.md && git add README.md && git -c user.name=t -c user.email=t@t commit -q -m sneak
designer_gate "$base" 2>/dev/null && { echo "FAIL gate: committed change outside design/brand passed"; exit 1; }
echo "ok   designer_gate"
