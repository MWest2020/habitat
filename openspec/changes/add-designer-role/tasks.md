# Tasks

- [x] Research and recommendation: `docs/explanation/designer-agent.md`.
- [x] `worker/design/` (`png.py`, `gates.py`, `check.py`, `kit.py`, `bin/`). Proof: `worker/test-design-check.sh` (11 gate tests, each gate caught on a fixture).
- [x] `worker/Containerfile`: rsvg-convert, design venv, OFL fonts, logo-design skill, all pinned. Proof: a local build of that layer (same RUN lines) rendered a full delivery with `design-kit` and `design-check` passed it; `logo-tool render_png --which` found rsvg-convert; the skill has no `assets/library/` (2026-11-21).
- [x] Role plumbing: `worker/settings/designer.json` (Stop hook `stop-design-check.sh`), `worker/schemas/designer.json`, entrypoint gate, `dispatch.sh` accepts the role, deadline 3600 s.
- [x] `dispatch/designer.sh`: one run plus a draft PR.
- [x] `templates/agents/designer.md`; handbook seed PR.
- [x] `cage/rbac.yaml`: ServiceAccount `role-designer`.
- [x] `docs/reference/roles.md`, `docs/reference/dispatch.md`, roadmap evidence.
- [ ] After review and merge: worker-image build on the merge commit, `kubectl apply` of `cage/rbac.yaml`, handbook seed merged.
- [ ] First live run: `designer.sh MWest2020/bazibo docs/design/brand-brief.md`; draft PR on bazibo.
