## ADDED Requirements

### Requirement: A role's definition comes from the handbook at a pinned commit

When `HABITAT_HANDBOOK_REF` is set, the worker SHALL use
`docs/agents/seeds/<role>.md` of MWest2020/handbook at that commit as the
role file, stored outside the work tree, and SHALL stop the run when it cannot
be fetched; it SHALL NOT fall back to a copy in the target repository.

#### Scenario: The handbook seed is used

- **WHEN** a reviewer run starts with `HABITAT_HANDBOOK_REF` set to a handbook commit that has `docs/agents/seeds/reviewer.md`
- **THEN** that file is the role file, its body is in the prompt
- **AND** it does not appear in the role's commit

#### Scenario: A missing seed fails closed

- **WHEN** an architect run starts with a ref at which the handbook has no `docs/agents/seeds/architect.md`
- **THEN** the run stops with a non-zero exit and a `fail closed` log line
- **AND** the repository's `.claude/agents/architect.md` is not used

#### Scenario: Without a ref, the repo copy is a logged fallback

- **WHEN** a run starts without `HABITAT_HANDBOOK_REF`
- **THEN** the target repository's `.claude/agents/<role>.md` is the role file
- **AND** the log carries a `WARNING` naming the fallback
