## ADDED Requirements

### Requirement: Roles run with enforced minimal toolsets

The worker SHALL run every role with a deny-by-default permission
configuration (`--permission-mode dontAsk`, per-role `--settings`, and
`--setting-sources user` so a cloned repo cannot inject its own
settings/hooks) instead of `bypassPermissions`. The push credential SHALL
NOT be present in the agent subprocess environment. Architect, reviewer
and security roles SHALL have no Edit/Write capability and no unscoped
Bash; the builder role SHALL have write access plus only scoped commands,
with `git push`, `.env`, secret and credential paths denied. The
container remains the outer isolation boundary.

#### Scenario: Reviewer cannot write

- **WHEN** a reviewer run attempts an Edit/Write tool call
- **THEN** the call is denied by the permission layer and the run
  continues read-only, with the denial visible in the run log

### Requirement: Roles produce structured, gate-able output

Every role SHALL emit `--output-format json` conforming to a per-role
schema, including a machine-readable verdict; dispatch/orchestrator SHALL
derive PASS/FAIL from that field rather than free text, and a FAIL
verdict SHALL stop the chain pending human decision.

#### Scenario: Security FAIL stops the chain

- **WHEN** a security run returns verdict FAIL
- **THEN** no follow-up role is dispatched for that change until Mark
  decides

### Requirement: Architect role plans without building

The architect role SHALL produce a plan (files, steps, boundaries,
verification criteria per builder task) as structured output, and SHALL
NOT modify repository files.

#### Scenario: Architect run leaves the tree clean

- **WHEN** an architect run completes
- **THEN** the working tree is unchanged and the plan is present in the
  structured output
