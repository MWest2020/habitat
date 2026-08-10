#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Unittest voor pretooluse-guard.sh: legt allow/deny per geval vast.
# allow = guard geeft geen deny-beslissing (lege output, exit 0).
# deny  = guard print permissionDecision:deny.
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
GUARD="$HERE/pretooluse-guard.sh"
fails=0

# check <verwacht: allow|deny> <omschrijving> <json-payload>
check() {
  local want=$1 desc=$2 payload=$3 out got
  out=$(printf '%s' "$payload" | bash "$GUARD" 2>/dev/null)
  if printf '%s' "$out" | grep -q '"permissionDecision":"deny"'; then got=deny; else got=allow; fi
  if [ "$got" = "$want" ]; then
    printf 'ok   %-6s %s\n' "$got" "$desc"
  else
    printf 'FAIL want=%s got=%s %s\n' "$want" "$got" "$desc"
    fails=$((fails+1))
  fi
}

rd() { printf '{"tool_name":"Read","tool_input":{"file_path":"%s"}}' "$1"; }
wr() { printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$1"; }
bash_cmd() { printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$1"; }

# --- rol-definitie: lezen mag, schrijven niet ---
check allow "Read .claude/agents/architect.md (rel)"      "$(rd '.claude/agents/architect.md')"
check allow "Read /work/repo/.claude/agents/builder.md"   "$(rd '/work/repo/.claude/agents/builder.md')"
check deny  "Write .claude/agents/architect.md"           "$(wr '.claude/agents/architect.md')"

# --- credentials/secrets onder .claude blijven dicht ---
check deny  "Read .claude/.credentials.json"              "$(rd '/work/repo/.claude/.credentials.json')"
check deny  "Read ~/.claude/.credentials.json"            "$(rd '/root/.claude/.credentials.json')"
check deny  "Read /var/run/claude/credentials.json"       "$(rd '/var/run/claude/credentials.json')"
check deny  "Read .claude/settings.json (niet-agents)"    "$(rd '/work/repo/.claude/settings.json')"

# --- overige secret-paden ---
check deny  "Read .env"                                    "$(rd '/work/repo/.env')"
check deny  "Read id_rsa"                                  "$(rd '/home/x/.ssh/id_rsa')"
check deny  "Read something.pem"                           "$(rd '/work/repo/tls/server.pem')"

# --- gewone repobestanden mogen ---
check allow "Read openspec/project.md"                    "$(rd '/work/repo/openspec/project.md')"
check allow "Read README.md"                              "$(rd 'README.md')"

# --- Bash: push en secret-lezers dicht ---
check deny  "Bash git push"                               "$(bash_cmd 'git push origin main')"
check deny  "Bash cat .env"                               "$(bash_cmd 'cat .env')"
check deny  "Bash grep /var/run/claude"                   "$(bash_cmd 'grep x /var/run/claude/credentials.json')"
check allow "Bash ls"                                     "$(bash_cmd 'ls -la')"

# --- pad-traversal mag de credential niet binnenhalen via de agents-uitzondering ---
check deny  "Read .claude/agents/../.credentials.json"    "$(rd '.claude/agents/../.credentials.json')"

if [ "$fails" -eq 0 ]; then
  echo "ALLE GUARD-TESTS GESLAAGD"
  exit 0
fi
echo "GUARD-TESTS GEFAALD: $fails"
exit 1
