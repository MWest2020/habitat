# Tasks

## 1. The sidecar
- [x] `dispatch/job-template.yaml`: the `testdb` native sidecar
      (`postgres:16-alpine`, uid 70, capabilities dropped, emptyDir PGDATA,
      `pg_isready` startup probe, 20m/64Mi requests) and the two env vars on
      the worker. Proof: `kubectl apply --dry-run=server` on a rendered Job.

## 2. Live
- [x] A rendered Job with the worker image, its command replaced by a
      connect-and-query, completes on the cluster and its log shows the
      server version. Proof: the Job log.
- [ ] The next wordsworth build's builder runs the DB tests instead of
      skipping them. Proof: its run output names the DB tests as run.

## 3. Docs
- [x] `docs/reference/dispatch.md`: the sidecar, the env vars, and why.
