#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Fetch a role's execution seed from the handbook at a pinned ref.
#
# Mark, 2026-10-25: "the cleanest is all looks at the handbook and there is where
# we have or index our agents and skills, consumed by habitat for whatever
# project". The handbook's docs/agents/seeds/<role>.md is the one definition of a
# role; habitat reads it at a commit SHA, so a run is reproducible and a change
# to a role is a handbook commit, not an edit in every target repository.
#
# Sourced by entrypoint.sh; also runnable on its own (the test calls it that way):
#   role-seed.sh <role> <ref> <base-url> <dest-file>
# <base-url> is e.g. https://raw.githubusercontent.com/MWest2020/handbook; the
# file fetched is <base-url>/<ref>/docs/agents/seeds/<role>.md. python3 does the
# fetch because the worker image has no curl; urllib also reads file:// URLs,
# which is how the test runs without a network.
#
# Exit codes: 0 fetched; 2 bad role name; 3 bad ref; 4 fetch failed or no such
# seed; 5 the fetched file is not a role definition (no front matter).

fetch_role_seed() {
  local role=$1 ref=$2 base=$3 dest=$4
  case "$role" in
    ""|*[!a-z0-9-]*|-*) echo "role-seed: role name is not a slug: '${role}'" >&2; return 2 ;;
  esac
  if ! [[ "$ref" =~ ^[0-9a-f]{7,40}$ ]]; then
    echo "role-seed: HABITAT_HANDBOOK_REF is not a commit SHA (7-40 hex): '${ref}'" >&2
    return 3
  fi
  local url="${base%/}/${ref}/docs/agents/seeds/${role}.md"
  mkdir -p "$(dirname "$dest")"
  if ! python3 - "$url" "$dest" <<'PY'
import sys, urllib.request
url, dest = sys.argv[1], sys.argv[2]
try:
    with urllib.request.urlopen(url, timeout=30) as r:
        data = r.read()
except Exception as exc:  # HTTP 404, DNS, missing file: all mean "no seed"
    sys.stderr.write(f"role-seed: cannot fetch {url}: {type(exc).__name__}: {exc}\n")
    sys.exit(1)
open(dest, "wb").write(data)
PY
  then
    rm -f "$dest"
    return 4
  fi
  # A 200 that is not a role definition (an HTML error page, an empty file) must
  # not become the prompt: a seed starts with YAML front matter.
  if [ "$(head -1 "$dest")" != "---" ]; then
    echo "role-seed: ${url} is not a role definition (no front matter)" >&2
    rm -f "$dest"
    return 5
  fi
  echo "role-seed: ${role} from handbook@${ref} (${url})" >&2
}

# Decide where this run's role file comes from; sets ROLE_FILE and ROLE_SOURCE.
#   resolve_role_file <role> <ref-or-empty> <base-url> <seed-dir>
# With a ref: the handbook seed, fetched to <seed-dir>/<role>.md (outside the
# work tree), or return 1 (fail closed). Without: the repo's own
# .claude/agents/<role>.md, with a warning on stderr (migration fallback).
resolve_role_file() {
  local role=$1 ref=$2 base=$3 dir=$4
  if [ -n "$ref" ]; then
    ROLE_FILE="${dir%/}/${role}.md"
    if ! fetch_role_seed "$role" "$ref" "$base" "$ROLE_FILE"; then
      echo "role-seed: no handbook seed for '${role}' at '${ref}', stopping (fail closed)" >&2
      return 1
    fi
    ROLE_SOURCE="the handbook (MWest2020/handbook@${ref}, docs/agents/seeds/${role}.md)"
  else
    ROLE_FILE=".claude/agents/${role}.md"
    ROLE_SOURCE="this repository's ${ROLE_FILE}"
    echo "role-seed: WARNING HABITAT_HANDBOOK_REF unset, using the repo copy ${ROLE_FILE} (migration fallback)" >&2
  fi
  export ROLE_FILE ROLE_SOURCE
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  set -euo pipefail
  [ $# -eq 4 ] || { echo "usage: role-seed.sh <role> <ref> <base-url> <dest-file>" >&2; exit 64; }
  fetch_role_seed "$@"
fi
