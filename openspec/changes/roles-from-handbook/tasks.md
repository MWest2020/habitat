# Tasks

- [x] `worker/role-seed.sh`: fetch + validate + resolve. Proof: `bash worker/test-role-seed.sh` (14 cases, no network), and a live fetch of the reviewer seed at handbook `1cbeafb`.
- [x] `worker/entrypoint.sh`: role file from the handbook at the ref, outside the work tree; body inlined in the prompt; fail closed.
- [x] `dispatch/dispatch.sh`, `dispatch/job-template.yaml`: pass `HABITAT_HANDBOOK_REF`.
- [x] `worker/Containerfile`: ship `role-seed.sh`. CI: `role-seed-tests` step.
- [x] Docs: `docs/reference/dispatch.md`, `docs/reference/roles.md`, `docs/explanation/architecture.md`.
- [ ] Handbook: an architect seed (Mark's gate: docs/agents).
- [ ] Live: a chain runs with `HABITAT_HANDBOOK_REF` set (new image pin + factory.yml).
- [ ] Remove the repo copies of `.claude/agents/` once every caller sets the ref.
