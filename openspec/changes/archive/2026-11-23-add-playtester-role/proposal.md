# A playtester role: someone looks at the result

## Why

Mark, 2026-11-09: *"ja, repareer de fabriek, begin met de speeltest-rol."* The
bubbels2 experiment (ratatoskr `docs/explanation/lessons-agent-factory.md`)
and convergence's "failed screen" share a cause: no role in the chain ever
opens the app and looks at it. Architect, builder, reviewer and security read
code. The Bubbels session that went well had a play-tester that played the
game in headless Chromium, read its screenshots, and a fix round after.

## What changes

- A fifth role, `playtester`, after reviewer and before security. It serves
  the app inside the cage, opens it in headless Chromium at phone and desktop
  size, plays what the change specifies, **reads its screenshots**, checks
  console errors and outside requests, and gives PASS or FAIL with findings in
  the reviewer's schema plus a `screenshots` list.
- Opt-in per repository: `.factory/playtest.yml` with `paths` globs, and
  `serve_dir` or `serve_cmd`, `viewports`, `checks`. `dispatch/playtest_gate.py`
  runs the role only when the change touches one of the paths.
- The worker image gets Python Playwright 1.56.0 with its Chromium headless
  shell, and `playtest-shoot` (`worker/playtest/shoot.py`).
- The role is read-only; its work tree is reset after the run. Up to 12
  screenshots travel out with the run artifacts (`playtest-*.jpg`).
- On FAIL the chain stops like for any role. A fix round (builder again with
  the playtester's findings) is the next step, not this change.

The role definition lives in the handbook (`docs/agents/seeds/playtester.md`,
Mark's gate); `templates/agents/playtester.md` is the same text for the
migration fallback.
