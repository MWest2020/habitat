#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Tests for dispatch/playtest_gate.py (change add-playtester-role), without GitHub.
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
GATE="$HERE/dispatch/playtest_gate.py"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
fail=0
check() { # <want-exit> <name> ; env set by caller
  local want=$1 name=$2 got=0
  python3 "$GATE" o/r b >/dev/null || got=$?
  if [ "$got" = "$want" ]; then echo "ok   $name"; else echo "FAIL $name (exit $got, want $want)"; fail=1; fi
}
printf 'paths:\n  - web/**\n  - "src/ui/*.ts"\nserve_dir: web\n' > "$T/block.yml"
printf 'paths: [web/**, assets/*]\n' > "$T/flow.yml"

PLAYTEST_GATE_CONFIG="$T/missing.yml" PLAYTEST_GATE_CHANGED="web/index.html" check 1 "no config: skip"
PLAYTEST_GATE_CONFIG="$T/block.yml" PLAYTEST_GATE_CHANGED=$'README.md\nweb/js/main.js' check 0 "block list, web file: run"
PLAYTEST_GATE_CONFIG="$T/block.yml" PLAYTEST_GATE_CHANGED=$'README.md\ndocs/x.md' check 1 "block list, no UI file: skip"
PLAYTEST_GATE_CONFIG="$T/block.yml" PLAYTEST_GATE_CHANGED="src/ui/app.ts" check 0 "quoted glob: run"
PLAYTEST_GATE_CONFIG="$T/flow.yml" PLAYTEST_GATE_CHANGED="assets/logo.svg" check 0 "flow list: run"
PLAYTEST_GATE_CONFIG="$T/flow.yml" PLAYTEST_GATE_CHANGED="" check 1 "empty diff: skip"
exit "$fail"
