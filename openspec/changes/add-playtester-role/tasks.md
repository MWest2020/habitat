# Tasks

- [x] `worker/playtest/shoot.py` + `playtest-shoot` in the image. Proof: a local run on bazibo `web/` (4 screenshots, no errors).
- [x] `worker/Containerfile`: Playwright 1.56.0 + Chromium headless shell, pinned.
- [x] `cage/rbac.yaml`: ServiceAccount `role-playtester` (applied to the cluster 2026-11-09).
- [x] Role plumbing: `worker/settings/playtester.json`, `worker/schemas/playtester.json`, `entrypoint.sh` and `dispatch.sh` accept the role; work tree reset; screenshots to the artifacts (`report/habitat_report.py`).
- [x] `dispatch/playtest_gate.py` + `chain.sh`. Proof: `worker/test-playtest-gate.sh`.
- [x] `templates/agents/playtester.md`; handbook seed PR.
- [x] `docs/reference/roles.md`, `docs/reference/dispatch.md`.
- [ ] Live: one dispatch of the role against a repository with a UI, screenshots in the artifacts.
- [ ] ratatoskr: bump `worker_image`; bump `handbook_ref` once the seed is merged.
