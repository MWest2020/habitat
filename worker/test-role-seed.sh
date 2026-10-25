#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Tests for worker/role-seed.sh: where a run's role file comes from
# (roles-from-handbook, 2026-10-25). No network: the "handbook" is a file:// tree
# laid out like raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=role-seed.sh
. "$HERE/role-seed.sh"

T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
REF=0123456789abcdef0123456789abcdef01234567
mkdir -p "$T/hb/$REF/docs/agents/seeds"
printf -- '---\nname: reviewer\nmodel: sonnet\nskills: []\n---\n\nReview the diff.\n' \
  > "$T/hb/$REF/docs/agents/seeds/reviewer.md"
printf '<html>not a seed</html>\n' > "$T/hb/$REF/docs/agents/seeds/broken.md"
BASE="file://$T/hb"

fails=0
ok()   { echo "ok   $1"; }
bad()  { echo "FAIL $1"; fails=$((fails+1)); }

# 1. A valid ref uses the handbook seed, written outside the work tree.
if resolve_role_file reviewer "$REF" "$BASE" "$T/role" 2>"$T/err" \
   && [ "$ROLE_FILE" = "$T/role/reviewer.md" ] \
   && grep -q 'Review the diff.' "$ROLE_FILE" \
   && [[ "$ROLE_SOURCE" == *"handbook@$REF"* ]]; then
  ok "valid ref: the handbook seed is the role file"
else bad "valid ref: the handbook seed is the role file"; fi

# 2. A short SHA is accepted too (7 hex).
if fetch_role_seed reviewer "0123456" "$BASE" "$T/short.md" 2>/dev/null; rc=$?; [ $rc -eq 4 ]; then
  ok "short SHA passes validation (then fails only on the missing path)"
else bad "short SHA passes validation (rc=$rc)"; fi

# 3. An invalid ref is refused before any fetch.
for r in main "HEAD" "../etc" "0123456789abcdef0123456789abcdef012345678" "xyz1234"; do
  fetch_role_seed reviewer "$r" "$BASE" "$T/x.md" 2>/dev/null; rc=$?
  if [ $rc -eq 3 ] && [ ! -e "$T/x.md" ]; then ok "invalid ref refused: $r"
  else bad "invalid ref refused: $r (rc=$rc)"; fi
done

# 4. A role name that is not a slug is refused.
for role in "../x" "Reviewer" "" "-x"; do
  fetch_role_seed "$role" "$REF" "$BASE" "$T/y.md" 2>/dev/null; rc=$?
  if [ $rc -eq 2 ]; then ok "role name refused: '$role'"; else bad "role name refused: '$role' (rc=$rc)"; fi
done

# 5. A missing seed fails closed: non-zero, no role file, never the repo copy.
mkdir -p "$T/repo/.claude/agents"; echo "repo copy" > "$T/repo/.claude/agents/architect.md"
( cd "$T/repo" && resolve_role_file architect "$REF" "$BASE" "$T/role2" 2>"$T/err5" ); rc=$?
if [ $rc -ne 0 ] && [ ! -e "$T/role2/architect.md" ] && grep -q 'fail closed' "$T/err5"; then
  ok "missing seed fails closed"
else bad "missing seed fails closed (rc=$rc)"; fi

# 6. A fetched file without front matter is not a role definition.
fetch_role_seed broken "$REF" "$BASE" "$T/b.md" 2>/dev/null; rc=$?
if [ $rc -eq 5 ] && [ ! -e "$T/b.md" ]; then ok "non-seed content refused"
else bad "non-seed content refused (rc=$rc)"; fi

# 7. No ref: the repo copy, with a warning (migration fallback).
( cd "$T/repo" && resolve_role_file architect "" "$BASE" "$T/role3" 2>"$T/err7" \
  && [ "$ROLE_FILE" = ".claude/agents/architect.md" ] ); rc=$?
if [ $rc -eq 0 ] && grep -q 'WARNING' "$T/err7" && [ ! -e "$T/role3" ]; then
  ok "unset ref falls back to the repo copy with a warning"
else bad "unset ref falls back to the repo copy with a warning (rc=$rc)"; fi

echo
if [ $fails -eq 0 ]; then echo "role-seed: all tests passed"; else echo "role-seed: $fails failed"; exit 1; fi
