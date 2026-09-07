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
[ -n "$tool" ] || deny "guard: lege tool-naam"

# Verboden paden (secrets + credentials). Grens is "niet-bestandsnaam-teken" i.p.v.
# alleen start/slash, zodat een pad ook midden in een Bash-commando wordt gevangen
# (bv. 'cat .env', 'git show HEAD:.env', 'grep x /proc/self/environ').
b='(^|[^A-Za-z0-9_])'   # start of niet-woordteken (spatie, /, :, =, quote, --)
# `.git/` staat erbij omdat het GEEN gewone map is maar een uitvoeringskanaal: een
# agent die .git/hooks/pre-commit of .git/config (core.fsmonitor, filter.*.clean)
# schrijft, laat zijn code draaien tijdens de `git add`/`git commit` van de
# entrypoint — buiten de permissielaag, in het proces waar GIT_PAT stond, en de
# payload staat niet in de diff en niet op de gepushte branch.
secret_re="${b}\.env(\$|[^A-Za-z0-9])|/secrets/|\.pem(\$|[^A-Za-z0-9])|${b}id_rsa|\.credentials\.json(\$|[^A-Za-z0-9])|${b}\.claude/|/var/run/claude/|${b}proc/|${b}sys/|${b}\.git/"

# Dezelfde lijst zónder de `.env`-clausule. Nodig omdat één uitzondering op
# `.env` (zie hieronder) niet ook `/secrets/.env.example` mag vrijgeven: de
# carve-out moet precies één clausule overslaan, niet de hele regex.
secret_re_no_env="/secrets/|\.pem(\$|[^A-Za-z0-9])|${b}id_rsa|\.credentials\.json(\$|[^A-Za-z0-9])|${b}\.claude/|/var/run/claude/|${b}proc/|${b}sys/|${b}\.git/"

# `.env.example` en soortgenoten zijn gecommitte sjablonen ZONDER geheimen —
# elke repo heeft er een, en een builder moet ze in de pas kunnen houden met
# de configuratie die ze documenteren. De oude regel ving ze wel: gemeten op
# een builder-run (2026-09-08, change document-demo-env) die daarop terugviel
# op FAIL terwijl de taak volkomen legitiem was.
#
# Alleen exacte basenames, verankerd op het einde: `.env.example.local` of
# `.env.example/../.env` matcht niet. De uitzondering geldt UITSLUITEND voor
# de padtools (Read/Edit/Write), niet voor Bash — een Bash-commando is vrije
# tekst waarin een sjabloonnaam een echte read kan meesmokkelen
# (`cat .env.example .env`), en een builder bewerkt een sjabloon met Edit,
# niet met cat.
env_template_re='(^|/)\.env\.(example|sample|template|dist|defaults)$'

# Weiger `fp` als het een verboden pad is, met de sjabloon-uitzondering.
deny_path_unless_env_template() {
  fp_=$1
  if printf '%s' "$fp_" | grep -Eq "$secret_re_no_env"; then
    deny "secrets-/credential-pad geblokkeerd"
  fi
  if printf '%s' "$fp_" | grep -Eq "${b}\.env(\$|[^A-Za-z0-9])"; then
    printf '%s' "$fp_" | grep -Eq "$env_template_re" \
      || deny "secrets-/credential-pad geblokkeerd"
  fi
}

case "$tool" in
  Bash)
    cmd=$(jq -r '.tool_input.command // ""' <<<"$payload") || deny "guard: command niet te parsen"
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
  Read)
    fp=$(jq -r '.tool_input.file_path // ""' <<<"$payload")
    # Newline in een pad is pathologisch: grep is regel-georiënteerd, dus een
    # meerregelig pad kan de uitzondering-regex op één regel matchen. Faalt-dicht.
    case "$fp" in *$'\n'*) deny "ongeldig pad (newline)" ;; esac
    # Rol-definitie mag gelezen worden: de worker draagt elke rol op de
    # .claude/agents/<rol>.md van de doelrepo te volgen. Alleen lezen, alleen
    # onder agents/, alleen .md.
    if printf '%s' "$fp" | grep -Eq '(^|/)\.claude/agents/[^/]+\.md$'; then
      # De uitzondering mag geen credential binnenhalen via een symlink — noch de
      # eindcomponent (rol.md -> .credentials.json) noch een gesymlinkte tussenmap
      # (.claude of .claude/agents -> elders). Weiger als ÉNIGE component in het
      # pad een symlink is. Dependency-vrij (alleen [ -L ] + expansie); een niet-
      # bestaand pad heeft geen symlink-componenten en valt gewoon door naar allow.
      d=$fp
      while [ -n "$d" ] && [ "$d" != "/" ] && [ "$d" != "." ]; do
        if [ -L "$d" ]; then deny "symlink in rol-definitiepad — geweigerd"; fi
        case "$d" in */*) d=${d%/*} ;; *) break ;; esac
      done
      exit 0
    fi
    deny_path_unless_env_template "$fp"
    ;;
  Edit|Write|NotebookEdit)
    fp=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // ""' <<<"$payload")
    # Newline in een pad: zelfde reden als bij Read — grep is regel-georienteerd.
    case "$fp" in *$'\n'*) deny "ongeldig pad (newline)" ;; esac
    # Geen uitzondering voor schrijven op .claude/ — dat blijft volledig dicht;
    # de enige carve-out is het env-sjabloon, zie deny_path_unless_env_template.
    deny_path_unless_env_template "$fp"
    ;;
esac
exit 0
