# The builder gets an hour

## Why

Since `worker-test-database` (2026-10-24) a builder runs a repository's
database tests instead of skipping them. The next wordsworth build
(`pilot-ingest-manifest`, wordsworth#221) hit the Job deadline:
`FailureTarget=DeadlineExceeded` after 1800 s, no run report, and the day's
last build slot spent. Earlier builders of the same change took 21 to 24
minutes without the DB tests.

## What changes

`dispatch/dispatch.sh` defaults `ACTIVE_DEADLINE_SECONDS` to 3600 for the
builder role and keeps 1800 for architect, reviewer and security. An explicit
`ACTIVE_DEADLINE_SECONDS` still wins. The token-expiry warning and the
dispatch wait (deadline + 600 s) follow from it unchanged.
