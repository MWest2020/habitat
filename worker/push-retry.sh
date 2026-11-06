#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Retry a role's branch push a few times before the Job fails (worker-push-retry).
#
# 2026-11-04: a wordsworth reviewer passed architect, builder and reviewer (PASS,
# no findings), then lost the whole run to a one-off GitHub server error on
# `git push` under `set -e` (BackoffLimitExceeded). The branch is run-unique
# (carries HABITAT_RUN_ID), so a retried push is always the same branch, never a
# force push and never a collision with another run.
#
# Sourced by entrypoint.sh; also runnable standalone (the test calls it that way):
#   push-retry.sh <branch>
#
# PUSH_ATTEMPTS (default 4) attempts, waiting PUSH_WAITS (default "5 15 45",
# space-separated seconds) between them. Returns 0 on the first success, the
# last attempt's exit code once every attempt has failed.

push_with_retry() {
  local branch=$1
  local attempts=${PUSH_ATTEMPTS:-4}
  local -a waits
  read -ra waits <<< "${PUSH_WAITS:-5 15 45}"
  local attempt=1 rc=0
  while [ "$attempt" -le "$attempts" ]; do
    if git push -u origin "$branch"; then
      [ "$attempt" -gt 1 ] && echo "push-retry: succeeded on attempt ${attempt}/${attempts}" >&2
      return 0
    fi
    rc=$?
    echo "push-retry: attempt ${attempt}/${attempts} failed (exit ${rc})" >&2
    if [ "$attempt" -lt "$attempts" ]; then
      sleep "${waits[$((attempt-1))]:-0}"
    fi
    attempt=$((attempt+1))
  done
  echo "push-retry: all ${attempts} attempts failed, giving up" >&2
  return "$rc"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  set -euo pipefail
  [ $# -eq 1 ] || { echo "usage: push-retry.sh <branch>" >&2; exit 64; }
  push_with_retry "$1"
fi
