# Roles come from the handbook, at a pinned commit

## Why

Mark, 2026-10-25: *"the cleanest is all looks at the handbook and there is
where we have or index our agents and skills, consumed by habitat for whatever
project"*. The handbook already calls `docs/agents/` the canonical registry,
but habitat read each target repo's own `.claude/agents/<role>.md`, and those
copies drifted: convergence's and wordsworth's builder, reviewer and security
differ from the handbook's seeds by 22 to 35 lines, and convergence carries an
architect the handbook has no seed for.

## What changes

- The worker fetches `docs/agents/seeds/<role>.md` from MWest2020/handbook at
  `HABITAT_HANDBOOK_REF` (a commit SHA) into `/work/role/<role>.md`, outside
  the work tree, so the role's commit never contains it. Model and skills come
  from its front matter as before; its body is inlined into the prompt.
- With the ref set, an invalid ref, a non-slug role, a missing seed or a file
  without front matter stops the run (fail closed). Without the ref, the repo
  copy is used with a warning: a migration fallback.
- `dispatch.sh` passes `HABITAT_HANDBOOK_REF` into the Job.
- No image pin is bumped here; setting the ref is the caller's step, after the
  handbook has a seed for every role a chain runs (architect is missing).
