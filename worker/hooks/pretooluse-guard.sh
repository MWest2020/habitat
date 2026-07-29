#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Tweede verdedigingslaag naast de permissions-deny-lijst (deny-rules kenden
# een afdwingbug — zie change add-role-architecture, research.md E): blokkeer
# git push en secrets-paden hard, ongeacht de allowlist.
set -u
payload=$(cat)

deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}

tool=$(jq -r '.tool_name // ""' <<<"$payload")

if [ "$tool" = "Bash" ]; then
  cmd=$(jq -r '.tool_input.command // ""' <<<"$payload")
  case "$cmd" in
    *"git push"*) deny "git push is voorbehouden aan de worker-entrypoint" ;;
  esac
fi

case "$tool" in
  Read|Edit|Write)
    fp=$(jq -r '.tool_input.file_path // ""' <<<"$payload")
    case "$fp" in
      *"/.env"|*"/.env."*|*"/secrets/"*|*.pem|*id_rsa*)
        deny "secrets-pad geblokkeerd" ;;
    esac
    ;;
esac
exit 0
