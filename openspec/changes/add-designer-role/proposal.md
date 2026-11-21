# A designer role: a brand delivery drawn in code, with its own gates

## Why

Mark, 2026-11-21: *"Zelf een ontwerper agent maken. Research is ok. Zal vast
goede agents beschikbaar zijn. Die in habitat brengen."* Bazibo needs a brand
redo (logo, palette, icons, store art, tokens) from its brief
`docs/design/brand-brief.md`. The handbook's `ontwerper` only advises in chat;
no role in the cage can draw, export and check a delivery. The roadmap item
"An execution role for the designer (ontwerper)" is this change.

Research and the choices behind it: `docs/explanation/designer-agent.md`.

## What changes

- A sixth role, `designer`. It reads a brief (`HABITAT_TASK_REF`), builds 2-3
  directions and one full delivery under `design/brand/` in the target repo:
  SVG logo set with PNGs, Play icon 512, App Store icon 1024, adaptive icon
  layers (432 px = 108 dp at 4x), feature graphic 1024x500, screenshot frames
  1080x1920 (NL, EN), `tokens.json` + `tokens.css`, `rationale.md`,
  `LICENSES.md`. Vector by code only; no image models.
- Its own gate, `design-check` (`worker/design/`, standard library only):
  layout, 2-3 directions, WCAG AA on every palette (text 4.5:1, accents 3:1),
  OFL fonts only, SVG hygiene (no external refs, `<text>`, `<image>`, inline
  styles, id clashes), exact PNG sizes and alpha, adaptive safe circle (66/108)
  and Play keyline, a legibility heuristic at 24 px, licences listed. It runs as
  the role's Stop hook and once more in the entrypoint: a claimed PASS with a
  failing delivery fails the run.
- Hardening from the independent review (2026-11-21): the entrypoint runs the
  gate as `env -u GIT_PAT HOME=/nonexistent design-gate.sh` with `python3 -I`;
  the SVG gate is an allowlist on parsed values; and, for **every** role, the
  entrypoint's git reads no global or system config and restores `.git/config`
  after the run (`worker/git-safe.sh`), so config an agent writes cannot run
  code while `GIT_PAT` is set.
- The worker image gets `rsvg-convert` (Debian), a venv with Pillow and
  fontTools (`design-kit`: render, text2path, contrast, fonts), the brief's OFL
  fonts from google/fonts at a pinned commit, and the MIT logo-design skill
  (kaankiziltug/logo-design-skill) at a pinned commit without its library of
  third-party logos (`logo-tool`).
- `dispatch/designer.sh <repo> <brief> [label]` dispatches one designer run and
  opens a **draft** PR from its branch. Builder and designer get a 3600 s
  deadline; the wrapper defaults the budget to $15.
- ServiceAccount `role-designer` in `cage/rbac.yaml`.

The role definition lives in the handbook (`docs/agents/seeds/designer.md`,
Mark's gate, with an execution facet on `ontwerper`);
`templates/agents/designer.md` is the same text for the migration fallback.
