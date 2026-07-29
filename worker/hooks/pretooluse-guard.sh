#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Tweede verdedigingslaag naast de permissions-deny-lijst (deny-rules kenden een
# afdwingbug — zie change add-role-architecture, research.md E). Draait voor ALLE
# rollen. Faalt DICHT: bij een parse-/logicafout wordt de tool geweigerd, niet
# toegestaan (M6). Blokkeert push, secrets-paden (ook via Bash-lezers) en
# credential-locaties, ongeacht de allowlist.
set -euo pipefail

deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}

payload=$(cat) || deny "guard: geen payload leesbaar"
tool=$(jq -r '.tool_name // ""' <<<"$payload") || deny "guard: payload niet te parsen"

# Verboden paden (secrets + credentials + kernel), als één alternation.
secret_re='(^|/)\.env($|\.)|/secrets/|\.pem$|/id_rsa|\.credentials\.json$|/\.claude/|/var/run/claude/|^/proc/|^/sys/'

case "$tool" in
  Bash)
    cmd=$(jq -r '.tool_input.command // ""' <<<"$payload")
    # git push in elke vorm (spaties/tabs/-C/env-prefix, argumenten ertussen).
    # Bewust breed: 'git' én een los 'push'-woord in hetzelfde commando -> deny.
    if printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]])git([[:space:]]|$)' \
       && printf '%s' "$cmd" | grep -Eq '(^|[[:space:]])push([[:space:]]|$)'; then
      deny "git push is voorbehouden aan de worker-entrypoint"
    fi
    # Een Bash-commando dat een verboden pad noemt (cat/grep/dd/... op .env etc.).
    if printf '%s' "$cmd" | grep -Eq "$secret_re"; then
      deny "commando raakt een secrets-/credential-pad"
    fi
    ;;
  Read|Edit|Write|NotebookEdit)
    fp=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // ""' <<<"$payload")
    if printf '%s' "$fp" | grep -Eq "$secret_re"; then
      deny "secrets-/credential-pad geblokkeerd"
    fi
    ;;
esac
exit 0
