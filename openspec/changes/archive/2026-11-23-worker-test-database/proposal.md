# Every worker has a throwaway test database

## Why

On 2026-10-24 the wordsworth change `pilot-ingest-manifest` (wordsworth#219)
went through the chain three times. The builder wrote the database
integration tests that carry the change's core claims: provenance reaches the
`register` audit record, a duplicate delivery is caught by the read-back, and
a layer that did not run fails the run. It never ran them. wordsworth's
`tests/conftest.py` starts a Postgres container or skips, and a worker can
start neither. So every DB test skipped, the builder said PASS, and:

- one build reached CI and failed there on a DB test with a wrong assertion
  (wordsworth PR #217), which no role could have seen;
- the next build's reviewer failed it, rightly: "written but never run".

odin, asked to decide, declined both a blind rebuild and weakening the
reviewer's check, and named this as the real fix. wordsworth's own AGENTS.md
says it: "A pytest run with skips is not 'every integration test ran'."

## What changes

- The worker Job gets a **native sidecar** (an init container with
  `restartPolicy: Always`): `postgres:16-alpine`, the image wordsworth's CI
  uses, on an `emptyDir`, reachable only on the pod's loopback. Its startup
  probe (`pg_isready`) holds the worker until the database answers. It stops
  with the worker.
- The worker gets `HABITAT_TEST_DATABASE_URL`, and the same value as
  `WORDSWORTH_TEST_DATABASE_URL` (the name wordsworth's conftest reads).
- The sidecar runs as the image's `postgres` user (uid 70) with every
  capability dropped and no privilege escalation, like the worker. The
  password is a fixed throwaway: the database lives and dies with the pod and
  is reachable from nowhere else.
- Requests are small (20m CPU, 64Mi). The work nodes have 1 CPU each, and
  dispatch.sh lowered the worker's request to 150m for that reason.

## Not in this change

- Other services (OpenSearch, S3, OpenAnonymiser). Their tests keep skipping
  in a worker; a repository that needs them says so in its own change.
- A per-repository switch. One small database for every role is simpler than
  a template per repo, and reviewer and security may run tests too.
