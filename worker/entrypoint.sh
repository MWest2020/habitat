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

# Optioneel: begin vanaf een bestaande branch (bv. reviewer/security bovenop de
# builder-branch) i.p.v. de default branch.
if [ -n "${HABITAT_BASE_BRANCH:-}" ]; then
  log "basis-branch: ${HABITAT_BASE_BRANCH}"
  git fetch --depth 50 origin "$HABITAT_BASE_BRANCH"
  git checkout -B "$HABITAT_BASE_BRANCH" FETCH_HEAD
fi

BRANCH="habitat/${HABITAT_ROLE}/${HABITAT_CHANGE}"
git checkout -b "$BRANCH"
BASE_REF=$(git rev-parse HEAD)   # basis vóór de agent; diff_hash meet hiertegen

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

# 4b. De agent kan tijdens de run zelf een branch hebben aangemaakt (bv. een
# change-taak "branch X vanaf de default branch"). Zonder correctie pusht stap 7
# dan een lege rol-branch en gaat het werk + run-report stilletjes verloren
# (les uit Wanderer-runs, 2026-07-12). Snap de rol-branch naar de huidige HEAD;
# working-tree-wijzigingen blijven staan.
CUR_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CUR_BRANCH" != "$BRANCH" ]; then
  log "agent eindigde op '$CUR_BRANCH' — rol-branch ${BRANCH} verplaatst naar diens HEAD"
  git checkout -q -B "$BRANCH"
fi

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

# 6. Stage de agent-wijziging, genereer hash-chained audit + HTML-run-rapport
git add -A
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 /opt/habitat/report/habitat_report.py \
  --repo-dir . --role "$HABITAT_ROLE" --change "$HABITAT_CHANGE" \
  --run-id "$HABITAT_RUN_ID" --verdict "$VERDICT" --subtype "$SUBTYPE" \
  --cost "$COST" --turns "$TURNS" --exit "$CLAUDE_EXIT" \
  --finished-at "$NOW" --repo "$REPO_URL" --base-ref "$BASE_REF"

# 6b. Bewaar de agent-eind-uitvoer (o.a. de review-tekst) als markdown op de branch.
# Ná habitat_report.py zodat dit de code-diff-hash niet vervuilt — net als
# run-report.json is dit een habitat-artefact, geen agent-codewijziging.
if jq -e 'has("result")' "$OUT" >/dev/null 2>&1; then
  OUTPUT_MD=".habitat/run-output-${HABITAT_RUN_ID}.md"
  {
    printf '# Habitat %s — %s\n\n' "$HABITAT_ROLE" "$HABITAT_CHANGE"
    printf '_run_id %s · verdict %s · %s_\n\n---\n\n' "$HABITAT_RUN_ID" "$VERDICT" "$NOW"
    jq -r '.result // ""' "$OUT"
  } > "$OUTPUT_MD"
  log "agent-uitvoer bewaard: ${OUTPUT_MD}"
fi

# 7. Commit + push — nooit main; we staan op $BRANCH
git add -A
git commit -q -m "habitat: ${HABITAT_ROLE} run ${HABITAT_RUN_ID} (change ${HABITAT_CHANGE})" \
  || log "commit: niets gewijzigd"
# Bestaat de remote branch al met andere historie (eerdere run), dan weigert de
# kale push en zou het run-report verloren gaan. Fallback: push naar een
# run-unieke branch zodat elke run altijd ergens landt. Nooit force-pushen.
git push -u origin "$BRANCH" || {
  log "push geweigerd — run bewaard op ${BRANCH}-${HABITAT_RUN_ID}"
  git push -u origin "HEAD:refs/heads/${BRANCH}-${HABITAT_RUN_ID}"
}
log "branch gepusht: ${BRANCH}"

# Exit weerspiegelt de run-uitkomst (Job-status)
[ "$VERDICT" = "ok" ] && exit 0 || exit 1
