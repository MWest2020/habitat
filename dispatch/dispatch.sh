#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Dispatch één rol-run als K8s-Job, stream de logs, en lees de uitkomst uit de
# Job-status (niet uit de pod-exit-code). Bare met opzet.
#   Gebruik: dispatch.sh <rol> <change> <repo> [run-id]
#   Env: WORKER_IMAGE (verplicht), KUBECTL, HABITAT_MAX_BUDGET_USD,
#        ACTIVE_DEADLINE_SECONDS, PAT_SECRET, HABITAT_LOGDIR
set -euo pipefail

ROLE=${1:?rol (builder|reviewer|security)}
CHANGE=${2:?change-naam}
REPO=${3:?doelrepo (owner/repo of URL)}
RUN_ID=${4:-${ROLE}-$(echo "$CHANGE" | tr '/_ ' '---')-$(date +%Y%m%d-%H%M%S)}

: "${WORKER_IMAGE:?zet WORKER_IMAGE=ghcr.io/mwest2020/habitat-worker:<sha>}"
KUBECTL=${KUBECTL:-kubectl}
HERE=$(cd "$(dirname "$0")" && pwd)

export JOB_NAME HABITAT_ROLE HABITAT_CHANGE HABITAT_REPO HABITAT_RUN_ID \
       HABITAT_MAX_BUDGET_USD ACTIVE_DEADLINE_SECONDS PAT_SECRET WORKER_IMAGE
HABITAT_ROLE=$ROLE HABITAT_CHANGE=$CHANGE HABITAT_REPO=$REPO HABITAT_RUN_ID=$RUN_ID
HABITAT_MAX_BUDGET_USD=${HABITAT_MAX_BUDGET_USD:-5.00}
ACTIVE_DEADLINE_SECONDS=${ACTIVE_DEADLINE_SECONDS:-1800}
PAT_SECRET=${PAT_SECRET:-pat-node-01}
slug=$(echo "$CHANGE" | tr '/_ ' '---' | tr '[:upper:]' '[:lower:]')
JOB_NAME="habitat-${ROLE}-${slug}-$(date +%s)"

VARS='$JOB_NAME $HABITAT_ROLE $HABITAT_CHANGE $HABITAT_REPO $HABITAT_RUN_ID'
VARS+=' $HABITAT_MAX_BUDGET_USD $ACTIVE_DEADLINE_SECONDS $PAT_SECRET $WORKER_IMAGE'

echo "[dispatch] Job=$JOB_NAME rol=$ROLE change=$CHANGE repo=$REPO"
envsubst "$VARS" < "$HERE/job-template.yaml" | $KUBECTL apply -f -

# Wacht tot de pod een terminale/lopende fase heeft, stream dan de logs
for _ in $(seq 1 60); do
  phase=$($KUBECTL -n agents get pods -l job-name="$JOB_NAME" \
           -o jsonpath='{.items[0].status.phase}' 2>/dev/null || true)
  case "$phase" in Running|Succeeded|Failed) break ;; esac
  sleep 2
done
$KUBECTL -n agents logs -f "job/$JOB_NAME" 2>/dev/null || true

# Log archiveren
LOGDIR=${HABITAT_LOGDIR:-./run-logs}
mkdir -p "$LOGDIR"
$KUBECTL -n agents logs "job/$JOB_NAME" > "$LOGDIR/$JOB_NAME.log" 2>/dev/null || true
echo "[dispatch] log: $LOGDIR/$JOB_NAME.log"

# Uitkomst uit Job.status.conditions (autoritatief)
conds=""
for _ in $(seq 1 30); do
  conds=$($KUBECTL -n agents get job "$JOB_NAME" \
           -o jsonpath='{range .status.conditions[?(@.status=="True")]}{.type}={.reason} {end}' \
           2>/dev/null || true)
  [ -n "$conds" ] && break; sleep 2
done
echo "[dispatch] condities: ${conds:-onbekend}"

if echo "$conds" | grep -qi 'Failed'; then
  reason=$(echo "$conds" | grep -o 'Failed=[^ ]*' | cut -d= -f2)
  if [ "$reason" = "DeadlineExceeded" ]; then
    echo "[dispatch] TIME-OUT — branch mogelijk deels/niet gepusht"
  else
    echo "[dispatch] MISLUKT (${reason:-onbekend})"
  fi
  exit 1
elif echo "$conds" | grep -qi 'Complete'; then
  echo "[dispatch] AFGEROND — lees run-report.json op branch habitat/${ROLE}/${CHANGE}"
  exit 0
fi
echo "[dispatch] onbekende status"; exit 2
