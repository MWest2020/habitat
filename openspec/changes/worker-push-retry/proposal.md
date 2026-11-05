# A role's branch push retries before the role fails

## Why

2026-11-04: wordsworth `originals-ingest-write` passed architect, builder and
reviewer (the reviewer's JSON verdict: `PASS`, no findings). The chain still
stopped, on the reviewer, because the worker's `git push` of the reviewer
branch got a one-off GitHub server error:

    remote: fatal error in commit_refs
     ! [remote rejected] habitat/reviewer/originals-ingest-write-… (failure)

`worker/entrypoint.sh` runs `git push` once under `set -e`, so the Job failed
(BackoffLimitExceeded) and the listener reported "reviewer: FAIL". A transient
error on GitHub's side threw away a passed role and cost a rebuild of the
whole chain (run file `wordsworth-originals-ingest-write-1793782969.log`).

## What changes

- Step 7 of `worker/entrypoint.sh` pushes through a small function
  `push_with_retry` in a new file `worker/push-retry.sh` (sourced, like
  `role-seed.sh`). It tries the push up to 4 times, waiting 5, 15 and 45
  seconds between attempts, and logs each failed attempt with its exit code.
- Only when all attempts fail does the push fail, and with it the Job, exactly
  as today. A push that succeeds on a later attempt is logged as such.
- The branch is unique per run (it carries the run id), so a repeated push is
  never a force push and never overwrites another run.
- A test (`worker/test-push-retry.sh`, run in `verify.yml` next to
  `test-role-seed.sh`) uses a fake `git` on `PATH`: fails twice then succeeds →
  success after 3 calls; always fails → failure after 4 calls; succeeds at once
  → 1 call. The waits are injectable so the test does not sleep.

## Deploy

The worker runs from a pinned image (`worker_image` in ratatoskr's
`agents/factory.yml`, one image per commit SHA). The fix takes effect only
after `worker-image.yml` builds the image for the merge commit and that pin is
bumped. Until then the old behaviour stays.

## Out of scope

- Retrying anything other than the branch push (clone, commit, the role run
  itself; the structured-output retry already exists in `dispatch/chain.sh`).
- Telling a transient push error apart from a permanent one: four attempts
  over about a minute is cheap either way.
