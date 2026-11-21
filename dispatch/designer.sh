#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Run the designer on a brief and open a draft PR with its delivery
# (change add-designer-role). One role, no chain: the delivery is a proposal
# for Mark, so the PR is a draft and nothing here merges.
#   Usage: designer.sh <owner/repo> <brief-path> [label]
#   Env:   everything dispatch.sh reads (WORKER_IMAGE, HABITAT_HANDBOOK_REF,
#          KUBECTL, HABITAT_AUTH, ...); HABITAT_MAX_BUDGET_USD defaults to 15.00
#          here; DESIGNER_NO_PR=1 skips the PR.
set -euo pipefail

# pr_body <brief> <run-id> <run-output-file>: the PR text. The agent's report is
# untrusted: it goes in a fenced block (no mentions, links, images or HTML take
# effect), with fences in it defused and the length capped.
pr_body() {
  echo "Brand delivery by the habitat designer for \`$1\` (run \`$2\`)."
  echo
  echo "Start with \`design/brand/rationale.md\` (directions and the recommendation)."
  echo "\`design-check\` passed in the run. A draft: review and choose before anything"
  echo "moves into the app; this PR does not change \`web/\`."
  if [ -f "$3" ]; then
    printf '\n## Designer report (agent output, verbatim)\n\n~~~~text\n'
    head -c 20000 "$3" | tr -d '\000-\010\013-\037' | sed -e 's/~~~/~ ~ ~/g' -e 's/```/` ` `/g'
    printf '\n~~~~\n'
  fi
}

main() {
  if [ $# -lt 2 ]; then
    echo "usage: designer.sh <owner/repo> <brief-path> [label]" >&2
    exit 64
  fi
  REPO=$1 BRIEF=$2
  LABEL=${3:-brand-$(date +%Y%m%d)}
  if ! [[ "$REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || [[ "$REPO" == *..* ]]; then
    echo "[designer] repo must be owner/repo: $REPO" >&2; exit 64
  fi
  case "$BRIEF" in
    /*|*..*|-*|""|*[!A-Za-z0-9_./-]*) echo "[designer] brief must be a path inside the repo: $BRIEF" >&2; exit 64 ;;
  esac
  case "$LABEL" in
    *[!a-z0-9-]*) echo "[designer] label must be a slug (a-z0-9-): $LABEL" >&2; exit 64 ;;
  esac
  HERE=$(cd "$(dirname "$0")" && pwd)

  # Fail before a Job exists when the brief is not on the default branch.
  if ! gh api "repos/${REPO}/contents/${BRIEF}" --jq .path >/dev/null 2>&1; then
    echo "[designer] brief not found in ${REPO}: ${BRIEF}" >&2
    exit 1
  fi

  RUN_ID="$(date +%Y%m%d-%H%M%S)-${RANDOM}"
  BRANCH="habitat/designer/${LABEL}-${RUN_ID}"
  export HABITAT_TASK_REF="$BRIEF"
  export HABITAT_MAX_BUDGET_USD=${HABITAT_MAX_BUDGET_USD:-15.00}

  rc=0
  "$HERE/dispatch.sh" designer "$LABEL" "$REPO" "$RUN_ID" || rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "[designer] run did not pass (exit $rc); no PR. Branch, if pushed: ${BRANCH}" >&2
    exit "$rc"
  fi
  if [ "${DESIGNER_NO_PR:-}" = 1 ]; then
    echo "[designer] DESIGNER_NO_PR=1: branch ${BRANCH}, no PR"
    exit 0
  fi

  repo_short=$(basename "$REPO" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-' | cut -c1-12)
  OUTPUT="${HABITAT_LOGDIR:-./run-logs}/artifacts/${repo_short}/${RUN_ID}/run-output-${RUN_ID}.md"
  BODY=$(mktemp); trap 'rm -f "$BODY"' EXIT
  pr_body "$BRIEF" "$RUN_ID" "$OUTPUT" > "$BODY"
  gh pr create --repo "$REPO" --draft --head "$BRANCH" \
    --title "Design: ${LABEL} (habitat designer, run ${RUN_ID})" --body-file "$BODY"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then main "$@"; fi
