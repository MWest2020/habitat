#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# designer_gate <base-ref>: the designer's post-run gate (change add-designer-role),
# sourced by entrypoint.sh, run in the work tree after the agent finished.
#  1. The designer writes only under design/brand/: any other changed or new path
#     (committed or not) fails the run. Its job is a proposal, not the app.
#  2. design-check design/brand passes, run from the image (the agent cannot
#     change the checker), whatever verdict the agent gave.
# Returns 0 when both hold; logs why not on stderr.
designer_gate() {
  local base=$1 outside
  outside=$( { git diff --name-only "$base"; git ls-files --others --exclude-standard; } \
             | sort -u | grep -v '^design/brand/' || true)
  if [ -n "$outside" ]; then
    printf '[habitat] designer changed paths outside design/brand/:\n%s\n' "$outside" >&2
    return 1
  fi
  if ! design-check design/brand >&2; then
    printf '[habitat] design-check: delivery gates failed\n' >&2
    return 1
  fi
  return 0
}
