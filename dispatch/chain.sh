#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Draai de volle rol-keten architect -> builder -> reviewer -> security en geef
# de (run-unieke) builder-branch door aan reviewer en security via
# HABITAT_BASE_BRANCH. Zo lezen die aantoonbaar de juiste builder-run, ook na
# een retry.
#   Gebruik: chain.sh <change> <repo>
#   Env: WORKER_IMAGE (verplicht), plus dezelfde env als dispatch.sh
#        (KUBECTL, CLAUDE_CREDS_FILE, HABITAT_LOGDIR, ...).
set -euo pipefail

CHANGE=${1:?change-naam}
REPO=${2:?doelrepo (owner/repo of URL)}
HERE=$(cd "$(dirname "$0")" && pwd)
: "${WORKER_IMAGE:?zet WORKER_IMAGE=ghcr.io/mwest2020/habitat-worker:<sha>}"

# Een geërfde waarde zou architect/builder ten onrechte op een basis-branch
# laten starten; die twee horen zonder base te draaien.
unset HABITAT_BASE_BRANCH

# Draai één rol; zet REPLY op de gepushte branch (uit "[dispatch] branch=...").
# Stopt de keten als dispatch niet-nul eindigt (Job Failed/onbekend) — een
# rol-FAIL houdt zo de volgende rollen tegen (verdicts sturen de keten).
run_role() {
  local role=$1 rc
  local log; log=$(mktemp)
  echo "=== keten: rol ${role} ==="
  set +e
  "$HERE/dispatch.sh" "$role" "$CHANGE" "$REPO" 2>&1 | tee "$log"
  rc=${PIPESTATUS[0]}
  set -e
  REPLY=$(grep -oE '^\[dispatch\] branch=habitat/[^[:space:]]+' "$log" | tail -1 | sed 's/.*branch=//') || REPLY=""
  rm -f "$log"
  if [ "$rc" -ne 0 ]; then
    echo "keten: rol ${role} niet geslaagd (dispatch exit ${rc})${REPLY:+ — branch ${REPLY}} — keten gestopt" >&2
    return 1
  fi
  [ -n "$REPLY" ] || { echo "keten: geen branch van rol ${role} — keten gestopt" >&2; return 1; }
  echo "keten: ${role} -> ${REPLY}"
}

run_role architect

run_role builder
builder_branch=$REPLY

# reviewer + security bouwen op de builder-branch
export HABITAT_BASE_BRANCH="$builder_branch"
run_role reviewer
run_role security
unset HABITAT_BASE_BRANCH

echo "keten klaar — builder-branch: ${builder_branch}"
