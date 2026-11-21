## ADDED Requirements

### Requirement: The entrypoint's git ignores config the agent can write

The worker entrypoint SHALL run git without system or global configuration,
taking the keys it needs (hooks off, fsmonitor off, its credential helper after
an empty helper that clears others, identity) from the environment, and SHALL
restore `.git/config` after the agent run from a copy kept in memory, then pin
`GIT_DIR`, `GIT_COMMON_DIR` and `GIT_WORK_TREE` to the repository. It SHALL fail
the run when `.git` or `.git/config` was replaced, when `.git/commondir`,
`.git/config.worktree` or `.git/worktrees/` exist, or when git still sees any
filter, diff or merge driver.

#### Scenario: An agent plants git config

- **WHEN** an agent writes a `core.fsmonitor` to `~/.gitconfig` and a filter driver and credential helper to `.git/config`
- **THEN** none of them runs in the entrypoint's add, commit, push or credential calls, and the credential helper used is the entrypoint's own

#### Scenario: An agent plants a commondir

- **WHEN** an agent writes `.git/commondir` pointing at a copy of `.git` whose config defines `filter.x.clean`, and `design/brand/.gitattributes` with `* filter=x`
- **THEN** the run fails before any entrypoint `git add`, and with the repository pinned the filter would not run either
