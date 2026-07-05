#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Habitat worker-entrypoint: clone doelrepo (PAT over HTTPS) -> claude -p in een rol
# -> push branch + run-report.json. Succes komt uit de JSON, niet uit de exit-code.
set -euo pipefail

log()  { printf '[habitat] %s\n' "$*" >&2; }
fail() { log "FOUT: $*"; exit 2; }

# 1. Verplichte env
for v in HABITAT_REPO HABITAT_ROLE HABITAT_CHANGE HABITAT_RUN_ID GIT_PAT; do
  [ -n "${!v:-}" ] || fail "env $v ontbreekt"
done
MAX_BUDGET="${HABITAT_MAX_BUDGET_USD:-5.00}"
export GIT_PAT

# 1b. Auth — sub-first: gemounte Claude-subscription-credentials; anders ANTHROPIC_API_KEY
CRED_SRC="${CLAUDE_CREDENTIALS_FILE:-/var/run/claude/credentials.json}"
if [ -f "$CRED_SRC" ]; then
  mkdir -p "$HOME/.claude"
  install -m 600 "$CRED_SRC" "$HOME/.claude/.credentials.json"
  log "auth: subscription-credentials"
elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  export ANTHROPIC_API_KEY
  log "auth: ANTHROPIC_API_KEY"
else
  fail "geen auth: mount claude-credentials of zet ANTHROPIC_API_KEY"
fi

# 2. Repo-URL (accepteer 'owner/repo', een volledige URL, of een lokaal pad)
case "$HABITAT_REPO" in
  *://*|/*|git@*) REPO_URL="$HABITAT_REPO" ;;
  *)             REPO_URL="https://github.com/${HABITAT_REPO}.git" ;;
esac

# 3. Git-auth zonder PAT-lek: credential-helper leest uit env, niet uit URL/reflog
git config --global credential.helper \
  '!f() { echo username=x-access-token; echo "password=${GIT_PAT}"; }; f'
git config --global user.email "habitat-worker@invalid.local"
git config --global user.name  "Habitat ${HABITAT_ROLE}"

WORK=/work/repo
rm -rf "$WORK"
log "clone ${REPO_URL}"
git clone --depth 50 "$REPO_URL" "$WORK"
cd "$WORK"

BRANCH="habitat/${HABITAT_ROLE}/${HABITAT_CHANGE}"
git checkout -b "$BRANCH"

# 4. Rol-prompt — rollen leven in .claude/agents/ van de DÓELREPO, niet in Habitat
PROMPT="Je bent de '${HABITAT_ROLE}'-agent voor deze repository. Volg
.claude/agents/${HABITAT_ROLE}.md en het project-CLAUDE.md, en werk aan de
OpenSpec-change '${HABITAT_CHANGE}'. Maak uitsluitend wijzigingen die bij die rol
en die change horen."

OUT=/work/claude-output.json
log "claude -p (rol=${HABITAT_ROLE}, budget=\$${MAX_BUDGET})"
set +e
claude -p "$PROMPT" \
  --output-format json \
  --permission-mode bypassPermissions \
  --max-budget-usd "$MAX_BUDGET" \
  > "$OUT" 2> /work/claude-stderr.log
CLAUDE_EXIT=$?
set -e

# 5. Verdict uit de JSON (defensief), niet uit de exit-code
VERDICT="error"; COST=""; TURNS=""; SUBTYPE=""
if jq -e . "$OUT" >/dev/null 2>&1; then
  # let op: `.is_error // true` is fout — jq behandelt false als leeg. Expliciet:
  IS_ERR=$(jq -r 'if .is_error == false then "false" else "true" end' "$OUT")
  SUBTYPE=$(jq -r '.subtype // ""' "$OUT")
  COST=$(jq -r '.total_cost_usd // ""' "$OUT")
  TURNS=$(jq -r '.num_turns // ""' "$OUT")
  [ "$IS_ERR" = "false" ] && VERDICT="ok" || VERDICT="failed"
else
  log "geen parseerbare JSON van claude (exit ${CLAUDE_EXIT})"
fi
log "verdict=${VERDICT} subtype=${SUBTYPE} cost=${COST} turns=${TURNS}"

# 6. run-report.json in de branch — duurzame audit, los van kubectl logs
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
jq -n \
  --arg role "$HABITAT_ROLE"   --arg change "$HABITAT_CHANGE" \
  --arg run_id "$HABITAT_RUN_ID" --arg repo "$REPO_URL" \
  --arg verdict "$VERDICT"     --arg subtype "$SUBTYPE" \
  --arg cost "$COST"           --arg turns "$TURNS" \
  --arg exit "$CLAUDE_EXIT"    --arg ts "$NOW" \
  '{role:$role, change:$change, run_id:$run_id, repo:$repo,
    verdict:$verdict, subtype:$subtype,
    total_cost_usd:($cost|tonumber?), num_turns:($turns|tonumber?),
    claude_exit:($exit|tonumber), finished_at:$ts}' \
  > run-report.json

# 7. Commit + push — nooit main; we staan op $BRANCH
git add -A
git commit -q -m "habitat: ${HABITAT_ROLE} run ${HABITAT_RUN_ID} (change ${HABITAT_CHANGE})" \
  || log "commit: niets gewijzigd"
git push -u origin "$BRANCH"
log "branch gepusht: ${BRANCH}"

# Exit weerspiegelt de run-uitkomst (Job-status)
[ "$VERDICT" = "ok" ] && exit 0 || exit 1
