#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Git for the entrypoint without config the agent can write (add-designer-role
# review, 2026-11-21). Sourced by entrypoint.sh.
#
# Every role runs as the same uid as the entrypoint, so ~/.gitconfig and
# .git/config are writable by the agent (the builder runs `make`, which runs
# anything). A core.fsmonitor, a filter driver or a credential helper written
# there would run in the entrypoint's own git calls after the run, while GIT_PAT
# is set. Two measures:
#  git_trusted_env      no system or global config at all; the keys the entrypoint
#                       needs come from the environment (command scope, which
#                       wins over the repo's config). An empty credential.helper
#                       first clears any helper the repo config adds.
#  git_snapshot_config  keeps .git/config in memory before the agent runs;
#  git_restore_config   puts it back after the run, and refuses a .git that is no
#                       longer a plain directory.

git_trusted_env() {
  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_COUNT=7
  export GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null
  export GIT_CONFIG_KEY_1=core.fsmonitor GIT_CONFIG_VALUE_1=false
  export GIT_CONFIG_KEY_2=credential.helper GIT_CONFIG_VALUE_2=
  # shellcheck disable=SC2016  # GIT_PAT is expanded by the helper, at push time
  export GIT_CONFIG_KEY_3=credential.helper \
         GIT_CONFIG_VALUE_3='!f() { echo username=x-access-token; echo "password=${GIT_PAT}"; }; f'
  export GIT_CONFIG_KEY_4=user.email GIT_CONFIG_VALUE_4=habitat-worker@invalid.local
  export GIT_CONFIG_KEY_5=user.name GIT_CONFIG_VALUE_5="Habitat ${HABITAT_ROLE:-worker}"
  export GIT_CONFIG_KEY_6=core.attributesFile GIT_CONFIG_VALUE_6=/dev/null
}

git_snapshot_config() {
  GIT_LOCAL_CONFIG=$(cat .git/config)
}

git_restore_config() {
  if [ -L .git ] || [ ! -d .git ] || [ -L .git/config ]; then
    echo "[habitat] .git or .git/config was replaced during the run (fail closed)" >&2
    return 1
  fi
  printf '%s\n' "$GIT_LOCAL_CONFIG" > .git/config
}
