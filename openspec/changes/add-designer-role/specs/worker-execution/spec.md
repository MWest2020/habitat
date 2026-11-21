## ADDED Requirements

### Requirement: The entrypoint's git ignores config the agent can write

The worker entrypoint SHALL run git without system or global configuration,
taking the keys it needs (hooks off, fsmonitor off, its credential helper after
an empty helper that clears others, identity) from the environment, and SHALL
restore `.git/config` after the agent run from a copy kept in memory, failing
the run when `.git` or `.git/config` was replaced.

#### Scenario: An agent plants git config

- **WHEN** an agent writes a `core.fsmonitor` to `~/.gitconfig` and a filter driver and credential helper to `.git/config`
- **THEN** none of them runs in the entrypoint's add, commit, push or credential calls, and the credential helper used is the entrypoint's own
