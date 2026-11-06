#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Tests for worker/push-retry.sh (worker-push-retry, 2026-11-04). A fake `git` on
# PATH, driven by a counter file, stands in for the real push.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=push-retry.sh
. "$HERE/push-retry.sh"

T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
export PUSH_WAITS="0 0 0"

fails=0
ok()  { echo "ok   $1"; }
bad() { echo "FAIL $1"; fails=$((fails+1)); }

make_fake_git() {
  # $1 = number of leading failures before a success ("always" = never succeeds)
  local fail_count=$1
  mkdir -p "$T/bin"
  cat > "$T/bin/git" <<EOF
#!/usr/bin/env bash
[ "\$1" = "push" ] || exit 0
COUNTER="$T/calls"
n=0
[ -f "\$COUNTER" ] && n=\$(cat "\$COUNTER")
n=\$((n+1))
echo "\$n" > "\$COUNTER"
if [ "$fail_count" = "always" ] || [ "\$n" -le "$fail_count" ]; then
  echo "fake git push failure #\$n" >&2
  exit 1
fi
exit 0
EOF
  chmod +x "$T/bin/git"
  rm -f "$T/calls"
}

run_with_fake_git() {
  PATH="$T/bin:$PATH" push_with_retry "habitat/builder/x-1" 2>"$T/err"
}

# 1. Succeeds at once: 1 call, exit 0.
make_fake_git 0
if run_with_fake_git && [ "$(cat "$T/calls")" = "1" ]; then
  ok "succeeds at once (1 call)"
else bad "succeeds at once (1 call, got $(cat "$T/calls" 2>/dev/null))"; fi

# 2. Fails twice then succeeds: 3 calls, exit 0, two failures logged.
make_fake_git 2
if run_with_fake_git && [ "$(cat "$T/calls")" = "3" ] \
   && [ "$(grep -c 'attempt .*failed' "$T/err")" = "2" ] \
   && grep -q 'succeeded on attempt 3/4' "$T/err"; then
  ok "fails twice then succeeds (3 calls, 2 logged failures)"
else bad "fails twice then succeeds (got $(cat "$T/calls" 2>/dev/null) calls)"; fi

# 3. Always fails: 4 calls, non-zero exit, four failures logged.
make_fake_git always
if ! run_with_fake_git; rc=$?; [ "$rc" -ne 0 ] && [ "$(cat "$T/calls")" = "4" ] \
   && [ "$(grep -c 'attempt .*failed' "$T/err")" = "4" ] \
   && grep -q 'all 4 attempts failed' "$T/err"; then
  ok "always fails (4 calls, non-zero exit)"
else bad "always fails (rc=$rc, calls=$(cat "$T/calls" 2>/dev/null))"; fi

echo
if [ $fails -eq 0 ]; then echo "push-retry: all tests passed"; else echo "push-retry: $fails failed"; exit 1; fi
