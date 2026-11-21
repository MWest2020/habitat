#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Stop gate (designer, change add-designer-role): the run may only end when
# design-check passes on design/brand/. The checker lives in the image, so the
# designer cannot change it; the entrypoint runs it once more after the run.
# Respects stop_hook_active: one block per stop cycle, no loop until the budget.
set -uo pipefail

payload=$(cat 2>/dev/null || echo '{}')
if [ "$(jq -r '.stop_hook_active // false' <<<"$payload" 2>/dev/null)" = "true" ]; then
  exit 0
fi
cd "${CLAUDE_PROJECT_DIR:-/work/repo}" 2>/dev/null || exit 0

out=$(timeout 300 design-check design/brand 2>&1); rc=$?
if [ "$rc" -ne 0 ]; then
  printf 'design-gate: design-check failed (exit %s); fix these before you finish:\n%s\n' "$rc" "$out" >&2
  exit 2
fi
exit 0
