#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Tests for worker/git-safe.sh: config the agent can write (~/.gitconfig,
# .git/config) runs nothing in the entrypoint's git calls after the run.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=git-safe.sh
. "$HERE/git-safe.sh"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
export HOME="$T/home" GIT_PAT=pat-123 HABITAT_ROLE=builder
mkdir -p "$HOME" "$T/repo"
fails=0
ok()  { echo "ok   $1"; }
bad() { echo "FAIL $1"; fails=$((fails+1)); }
evil="$T/evil.sh"
printf '#!/bin/sh\ntouch "%s/pwned-$1"\ncat >/dev/null\n' "$T" > "$evil"; chmod +x "$evil"

git_trusted_env
cd "$T/repo" && git init -q && echo a > a.txt && git add a.txt && git commit -q -m base
git_snapshot_config

# What an agent could write during its run:
printf '[core]\n\tfsmonitor = %s global\n[alias]\n\tstatus = !%s alias\n' "$evil" "$evil" > "$HOME/.gitconfig"
cat >> .git/config <<CFG
[core]
	fsmonitor = $evil local
[credential]
	helper = !$evil helper
[filter "x"]
	clean = $evil filter
CFG
echo '*.txt filter=x' > .gitattributes

git_restore_config || bad "restore refused a plain .git"
echo b > a.txt
git status --porcelain >/dev/null; git add -A; git commit -q -m after
out=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null || true)
if ls "$T"/pwned-* >/dev/null 2>&1; then bad "agent-written git config ran: $(ls "$T"/pwned-*)"
else ok "no fsmonitor, filter, alias or helper from agent-written config ran"; fi
case "$out" in *password=pat-123*) ok "our credential helper answers" ;;
  *) bad "credential helper missing: $out" ;; esac
[ "$(git log -1 --format=%an)" = "Habitat builder" ] && ok "identity from the environment" \
  || bad "identity: $(git log -1 --format=%an)"

# Restore refuses a replaced .git/config.
rm .git/config && ln -s "$T/elsewhere" .git/config
if git_restore_config 2>/dev/null; then bad "restore accepted a symlinked .git/config"
else ok "restore refuses a symlinked .git/config"; fi
exit "$fails"
