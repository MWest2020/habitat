## MODIFIED Requirements

### Requirement: Roles run with enforced minimal toolsets

The worker SHALL run every role with a deny-by-default permission
configuration (`--permission-mode dontAsk`, per-role `--settings`, and
`--setting-sources user` so a cloned repo cannot inject its own
settings/hooks) instead of `bypassPermissions`. The push credential SHALL
NOT be present in the agent subprocess environment. Architect, reviewer
and security roles SHALL have no Edit/Write capability and no unscoped
Bash; the builder role SHALL have write access plus only scoped commands,
with `git push`, secret and credential paths denied. The denied env-file
paths SHALL be the ones that conventionally hold filled-in secrets
(`.env` itself, and the environment-named and `.local` variants); a
committed, secret-free template such as `.env.example` SHALL remain
readable and writable, because a builder legitimately has to keep it in
step with the configuration it documents. The container remains the outer
isolation boundary.

#### Scenario: Reviewer cannot write

- **WHEN** a reviewer run attempts an Edit/Write tool call
- **THEN** the call is denied by the permission layer and the run
  continues read-only, with the denial visible in the run log

#### Scenario: A builder can update a committed env template

- **WHEN** a builder run edits `deploy/.env.example` (or another
  `.env.example`/`.env.sample` in the target repo) as part of its change
- **THEN** the edit is permitted, while a read of `.env`, `.env.local`,
  `.env.production` or another filled-in environment file is still denied

#### Scenario: A builder runs the repository's own gate

- **WHEN** a builder run calls `bash verify.sh`, `python3 -m unittest` or
  `python3 -m pytest` in the target repository
- **THEN** the command runs, while `python3 -c ...`, `bash -c ...` or a bare
  `python3 <script>` is still denied

