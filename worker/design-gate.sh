#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# design-gate.sh <base-ref>: the designer's post-run gate (change add-designer-role),
# run by entrypoint.sh in the work tree after the agent finished, as
# `env -u GIT_PAT HOME=/nonexistent design-gate.sh <base>` (no token, no $HOME).
#  1. The designer writes only under design/brand/: any other changed, deleted or
#     new path, committed or not, fails the run. --no-renames, so a move out of
#     web/ into design/brand/ counts as the deletion it is; NUL-separated, so a
#     file name with a newline cannot hide a path.
#  2. design-check design/brand passes, from the image, whatever the agent said.
# Exit 0 when both hold; says why not on stderr.
designer_gate() {
  local base=$1 f outside=""
  git rev-parse -q --verify "${base}^{commit}" >/dev/null \
    || { echo "[habitat] design-gate: base ${base} is not a commit" >&2; return 1; }
  while IFS= read -r -d '' f; do
    case "$f" in
      design/brand/*) ;;
      *) outside+="  ${f@Q}"$'\n' ;;
    esac
  done < <(git diff --name-only --no-renames --no-ext-diff -z "$base" --;
           git ls-files --others --exclude-standard -z)
  if [ -n "$outside" ]; then
    printf '[habitat] designer changed paths outside design/brand/:\n%s' "$outside" >&2
    return 1
  fi
  if ! design-check design/brand >&2; then
    printf '[habitat] design-check: delivery gates failed\n' >&2
    return 1
  fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  set -uo pipefail
  [ $# -eq 1 ] || { echo "usage: design-gate.sh <base-ref>" >&2; exit 64; }
  designer_gate "$1"
fi
