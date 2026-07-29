#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Stop-gate (builder): heeft de doelrepo een scripts/verify.sh, dan moet die
# slagen vóór de run mag eindigen. Deterministisch waar promptinstructies
# advisory zijn (change add-role-architecture, research.md A5).
#
# Hardening (M4/M7):
# - Draai de verify uit de BASIS-commit (BASE_REF), niet de door de builder
#   mogelijk aangepaste versie: de gate valt niet te ontwapenen door verify.sh
#   te wijzigen/verwijderen.
# - Respecteer stop_hook_active: één blokkade, geen eindeloze lus tot budget.
# - timeout rond de call zodat een hangende verify de Job niet ophoudt.
set -uo pipefail

payload=$(cat 2>/dev/null || echo '{}')
# Al eerder geblokkeerd in deze stop-cyclus? Dan doorlaten (geen lus).
if [ "$(jq -r '.stop_hook_active // false' <<<"$payload" 2>/dev/null)" = "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-/work/repo}" 2>/dev/null || exit 0
base="${HABITAT_BASE_REF:-}"

# verify.sh uit de basiscommit halen (kan de builder niet manipuleren).
script=""
if [ -n "$base" ] && git cat-file -e "${base}:scripts/verify.sh" 2>/dev/null; then
  script=$(mktemp)
  git show "${base}:scripts/verify.sh" > "$script" 2>/dev/null || { rm -f "$script"; exit 0; }
elif [ -x scripts/verify.sh ]; then
  script=scripts/verify.sh   # fallback: geen base bekend
else
  exit 0                     # geen verify in de repo -> geen gate
fi

out=$(timeout 300 bash "$script" 2>&1); rc=$?
[ "$script" != "scripts/verify.sh" ] && rm -f "$script"

if [ "$rc" -ne 0 ]; then
  printf 'verify-gate: scripts/verify.sh faalde (exit %s):\n%s\n' "$rc" "$out" >&2
  exit 2
fi
exit 0
