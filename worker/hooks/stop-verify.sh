#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Stop-gate (builder): heeft de doelrepo een scripts/verify.sh, dan moet die
# slagen vóór de run mag eindigen. Exit 2 blokkeert het stoppen — hooks zijn
# deterministisch waar promptinstructies advisory zijn (zie change
# add-role-architecture, research.md A5).
set -u
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || true
[ -x scripts/verify.sh ] || exit 0
out=$(scripts/verify.sh 2>&1); rc=$?
if [ "$rc" -ne 0 ]; then
  printf 'verify-gate: scripts/verify.sh faalde (exit %s). Los dit eerst op:\n%s\n' \
    "$rc" "$out" >&2
  exit 2
fi
exit 0
