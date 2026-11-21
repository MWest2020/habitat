#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Tests for the designer role (change add-designer-role), without the image:
# design-check's gates on fixture deliveries, and the role's config files.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
python3 -W error::ResourceWarning "$HERE/design/test_check.py"
python3 -W error::ResourceWarning "$HERE/design/test_svggate.py"
for f in "$HERE/settings/designer.json" "$HERE/schemas/designer.json"; do
  jq -e . "$f" >/dev/null || { echo "FAIL invalid JSON: $f"; exit 1; }
done
jq -e '.permissions.deny | index("WebFetch") and index("Bash(curl *)") and index("Bash(git push *)")' \
  "$HERE/settings/designer.json" >/dev/null || { echo "FAIL designer settings: network/push not denied"; exit 1; }
jq -e '.hooks.Stop[0].hooks[0].command == "/opt/habitat/hooks/stop-design-check.sh"' \
  "$HERE/settings/designer.json" >/dev/null || { echo "FAIL designer settings: no Stop gate"; exit 1; }
D="$HERE/../dispatch/designer.sh"
for args in "" "o/r" "not-a-repo docs/b.md" "o/r/x docs/b.md" "../r docs/b.md" "o/r ../b.md" "o/r /etc/x" "o/r docs/b.md Bad_Label"; do
  rc=0; read -ra a <<<"$args"; bash "$D" "${a[@]}" >/dev/null 2>&1 || rc=$?
  [ "$rc" = 64 ] || { echo "FAIL designer.sh '$args': exit $rc, want 64"; exit 1; }
done
(
  # shellcheck source=../dispatch/designer.sh
  . "$D"
  o=$(mktemp); printf 'hi @mark ![t](https://t.example/p.png)\n~~~~\n```\n<b>x</b>\n' > "$o"
  b=$(pr_body docs/b.md r1 "$o"); rm -f "$o"
  [ "$(grep -c '^~~~~' <<<"$b")" = 2 ] || { echo "FAIL pr_body: agent output escaped its fence"; exit 1; }
  grep -q '^~~~~text$' <<<"$b" && grep -q '@mark' <<<"$b" || { echo "FAIL pr_body: report missing"; exit 1; }
) || exit 1
echo "ok   designer role config"

# The checker cannot be hijacked through the user site (.pth) the agent can write.
for w in "$HERE"/design/bin/*; do
  grep -Eq '^exec [^ ]*python3? -I ' "$w" || { echo "FAIL $w runs python without -I"; exit 1; }
done
grep -q 'env -u GIT_PAT HOME=/nonexistent' "$HERE/entrypoint.sh" \
  || { echo "FAIL entrypoint runs the design gate with the token or \$HOME"; exit 1; }
U=$(mktemp -d)
site=$(HOME="$U" python3 -c 'import site; print(site.getusersitepackages())')
mkdir -p "$site" "$U/empty" && echo 'import os; os._exit(0)' > "$site/evil.pth"
HOME="$U" python3 "$HERE/design/check.py" "$U/empty" >/dev/null 2>&1 \
  || echo "note: user-site .pth not honoured here; the -I check below still runs"
rc=0; HOME="$U" python3 -I "$HERE/design/check.py" "$U/empty" >/dev/null 2>&1 || rc=$?
rm -rf "$U"
[ "$rc" = 1 ] || { echo "FAIL design-check -I passed an empty delivery (exit $rc)"; exit 1; }
echo "ok   design-check ignores a planted user-site .pth"

# design-gate.sh: a fake design-check on PATH, a throwaway repo.
GATE="$HERE/design-gate.sh"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/repo"
printf '#!/bin/sh\nexit "${FAKE_CHECK_RC:-0}"\n' > "$T/bin/design-check"; chmod +x "$T/bin/design-check"
export PATH="$T/bin:$PATH"
g() { git -c user.name=t -c user.email=t@t "$@"; }
cd "$T/repo" && git init -q && mkdir web && echo a > web/index.html && g add -A && g commit -q -m base
base=$(git rev-parse HEAD)
gate() { # <want: pass|fail> <name>
  local rc=0; bash "$GATE" "$base" 2>/dev/null || rc=$?
  if { [ "$1" = pass ] && [ "$rc" = 0 ]; } || { [ "$1" = fail ] && [ "$rc" != 0 ]; }; then
    echo "ok   design-gate: $2"; else echo "FAIL design-gate: $2 (exit $rc)"; exit 1; fi
}
mkdir -p design/brand && echo x > design/brand/rationale.md
gate pass "delivery only, check passes"
FAKE_CHECK_RC=1 gate fail "design-check fails"
echo y > web/new.html; gate fail "new file outside design/brand"; rm web/new.html
g mv web/index.html design/brand/moved.html; gate fail "move out of web/ (a deletion)"
g mv design/brand/moved.html web/index.html
touch $'design/brand/ok\nweb-index.html'; gate pass "newline in a name inside design/brand"
rm design/brand/ok*; touch $'evil\nname'; gate fail "newline name outside design/brand"
rm evil*; echo z > README.md && g add README.md && g commit -q -m sneak
gate fail "committed change outside design/brand"
base=0000000; gate fail "base is not a commit"
