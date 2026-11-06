# Tasks

## 1. Push with retry

- [ ] `worker/push-retry.sh`: `push_with_retry <branch>` runs `git push -u origin <branch>` up to `PUSH_ATTEMPTS` (default 4) times, waiting `PUSH_WAITS` (default `5 15 45`) seconds between attempts; logs each failure with its exit code; returns 0 on the first success, the last exit code when all fail. Sourced, no side effects at source time.
- [ ] `worker/entrypoint.sh` step 7 sources it and calls `push_with_retry "$BRANCH"` instead of the bare `git push`. Under `set -e` the Job still fails when every attempt fails.

## 2. Test

- [ ] `worker/test-push-retry.sh`: a fake `git` on `PATH` driven by a counter file. Cases: succeeds at once (1 call, exit 0); fails twice then succeeds (3 calls, exit 0, two failures logged); always fails (4 calls, non-zero exit). `PUSH_WAITS="0 0 0"` so the test does not sleep.
- [x] CI runs `worker/test-push-retry.sh` without a workflow change: `verify.yml` runs every `worker/test-*.sh` (done outside the build; the builder's token may not edit workflows).

## 3. Docs

- [ ] `docs/reference/dispatch.md` (or the worker how-to it points to): one paragraph on the push retry, and that it needs the image pin bumped to take effect.
