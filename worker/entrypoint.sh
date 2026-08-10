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

# 1a. Rol-validatie + per-rol enforcement-config (change add-role-architecture):
# elke rol draait deny-by-default (dontAsk + allowlist) i.p.v. bypassPermissions.
# Bewuste afwijking van de research-aanbeveling: GEEN --bare — dat slaat de
# subscription-login over ("Not logged in", lokaal bewezen 2026-07-29) en habitat
# is sub-first. Determinisme komt van dontAsk + expliciete settings + gepind image.
case "$HABITAT_ROLE" in
  architect|builder|reviewer|security) ;;
  *) fail "onbekende rol '${HABITAT_ROLE}' (architect|builder|reviewer|security)" ;;
esac
ROLE_SETTINGS="/opt/habitat/settings/${HABITAT_ROLE}.json"
ROLE_SCHEMA="/opt/habitat/schemas/${HABITAT_ROLE}.json"
[ -f "$ROLE_SETTINGS" ] || fail "settings ontbreken: $ROLE_SETTINGS"
[ -f "$ROLE_SCHEMA" ]   || fail "schema ontbreekt: $ROLE_SCHEMA"

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

# Run-unieke branch: elke run landt op een eigen branch, nooit destructief en
# zonder force. De keten geeft de builder-branch expliciet door aan reviewer/
# security (HABITAT_BASE_BRANCH); zie dispatch/chain.sh.
BRANCH="habitat/${HABITAT_ROLE}/${HABITAT_CHANGE}-${HABITAT_RUN_ID}"
git checkout -b "$BRANCH"
BASE_REF=$(git rev-parse HEAD)   # basis vóór de agent; diff_hash meet hiertegen
export HABITAT_BASE_REF="$BASE_REF"   # stop-verify draait verify.sh uit deze commit

# 4. Rol-prompt — rollen leven in .claude/agents/ van de DÓELREPO, niet in Habitat
PROMPT="Je bent de '${HABITAT_ROLE}'-agent voor deze repository. Volg
.claude/agents/${HABITAT_ROLE}.md en het project-CLAUDE.md, en werk aan de
OpenSpec-change '${HABITAT_CHANGE}'. Maak uitsluitend wijzigingen die bij die rol
en die change horen."

OUT=/work/claude-output.json
log "claude -p (rol=${HABITAT_ROLE}, budget=\$${MAX_BUDGET})"
set +e
# Hardening (security-review B2/M3):
# - --setting-sources user: laad NIET de .claude/settings.json van de gekloonde
#   doelrepo (die kan hooks meebrengen die ongevraagd shell-exec geven). Onze
#   rol-settings komen expliciet via --settings; de enforcement blijft dus staan.
# - env -u GIT_PAT: de agent heeft de push-token niet nodig (clone/push doet de
#   entrypoint); zo kan repo-gecontroleerde code (Makefile/npm-script) niet
#   geauthenticeerd pushen buiten de permissielaag om.
env -u GIT_PAT claude -p "$PROMPT" \
  --output-format json \
  --json-schema "$(cat "$ROLE_SCHEMA")" \
  --settings "$ROLE_SETTINGS" \
  --setting-sources user \
  --permission-mode dontAsk \
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

# 4c. Architect plant, bouwt niet: wijzigingen worden teruggedraaid en de run
# faalt (spec role-architecture). Dekt zowel working-tree-wijzigingen als een
# door de agent gemaakte COMMIT (M9): hard-reset naar BASE_REF vóór de vergelijking.
ARCHITECT_DIRTY=0
if [ "$HABITAT_ROLE" = "architect" ]; then
  if [ "$(git rev-parse HEAD)" != "$BASE_REF" ] || [ -n "$(git status --porcelain)" ]; then
    log "architect wijzigde de repo (commit of working tree) — teruggedraaid, run afgekeurd"
    ARCHITECT_DIRTY=1
  fi
  git reset -q --hard "$BASE_REF"
  git clean -fdq
fi

# 5. Verdict uit de JSON (defensief), niet uit de exit-code
VERDICT="error"; COST=""; TURNS=""; SUBTYPE=""; ROLE_VERDICT=""
if jq -e . "$OUT" >/dev/null 2>&1; then
  # let op: `.is_error // true` is fout — jq behandelt false als leeg. Expliciet:
  IS_ERR=$(jq -r 'if .is_error == false then "false" else "true" end' "$OUT")
  SUBTYPE=$(jq -r '.subtype // ""' "$OUT")
  COST=$(jq -r '.total_cost_usd // ""' "$OUT")
  TURNS=$(jq -r '.num_turns // ""' "$OUT")
  [ "$IS_ERR" = "false" ] && VERDICT="ok" || VERDICT="failed"
  # Rol-verdict (PASS/FAIL) uit de structured output: machinaal gate-baar,
  # geen vrije tekst. Envelope-veld verschilt per CLI-versie -> defensief.
  ROLE_VERDICT=$(jq -r '
    (.structured_output.verdict? //
     (.result | strings | try fromjson | .verdict?) // "")' "$OUT" 2>/dev/null || echo "")
  # Fail-closed (reviewer major): een geslaagde run zonder machinaal PASS/FAIL
  # is geen groen licht. Alleen een expliciete PASS laat VERDICT=ok staan.
  case "$ROLE_VERDICT" in
    PASS) : ;;
    FAIL) log "rol-verdict FAIL — keten stopt hier (northstar 4)"; VERDICT="failed" ;;
    *)    log "geen machinaal rol-verdict (PASS/FAIL) in output — gate valt dicht"
          VERDICT="failed" ;;
  esac
else
  log "geen parseerbare JSON van claude (exit ${CLAUDE_EXIT})"
fi
[ "$ARCHITECT_DIRTY" = "1" ] && VERDICT="failed"

# 5b. Secret-detectie VÓÓR het rapport (reviewer minor): scan de agent-output
# (bron van run-output.md) en de werkboom; een hit maakt de run failed, zodat
# run-report.json en de Job-uitkomst niet tegenstrijdig zijn. De feitelijke
# redactie van bestanden gebeurt in stap 6c (vlak vóór de commit).
SECRET_RE='sk-ant-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|gho_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}'
# Alleen de agent-output en de door de agent gemaakte diff — niet de al
# bestaande repo-inhoud (dat zou op legitieme fixtures false-flaggen).
if grep -Eq "$SECRET_RE" "$OUT" 2>/dev/null \
   || git diff "$BASE_REF" 2>/dev/null | grep -Eq "$SECRET_RE"; then
  log "SECRET-SCAN: patroon in agent-output of -diff — run afgekeurd"
  VERDICT="failed"
fi
log "verdict=${VERDICT} rol-verdict=${ROLE_VERDICT:-geen} subtype=${SUBTYPE} cost=${COST} turns=${TURNS}"

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

# 6c. Secret-scrub: redigeer de waarde in alle te committen bestanden (SECRET_RE
# is in 5b gedefinieerd; de verdict-flip is daar al gebeurd). Defense-in-depth (B1).
git add -A
while IFS= read -r f; do
  [ -f "$f" ] || continue
  if grep -Eq "$SECRET_RE" "$f" 2>/dev/null; then
    log "SECRET-SCRUB: patroon geredigeerd in ${f}"
    sed -i -E "s/${SECRET_RE}/[REDACTED-SECRET]/g" "$f"
  fi
done < <(git diff --cached --name-only --diff-filter=ACM)

# 7. Commit + push — nooit main; we staan op $BRANCH
git add -A
git commit -q -m "habitat: ${HABITAT_ROLE} run ${HABITAT_RUN_ID} (change ${HABITAT_CHANGE})" \
  || log "commit: niets gewijzigd"
# De branch is uniek per run (bevat run-id), dus de push is altijd een nieuwe
# branch: geen collision, geen force, geen eerdere run overschreven.
git push -u origin "$BRANCH"
log "branch gepusht: ${BRANCH}"

# Exit weerspiegelt de run-uitkomst (Job-status)
[ "$VERDICT" = "ok" ] && exit 0 || exit 1
