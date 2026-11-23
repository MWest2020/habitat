## ADDED Requirements

### Requirement: A throwaway test database in every worker

Every worker Job SHALL run a PostgreSQL 16 database as a native sidecar,
reachable only on the pod's loopback, started before the worker and stopped
with it, and SHALL give the worker its connection URL as
`HABITAT_TEST_DATABASE_URL` and as `WORDSWORTH_TEST_DATABASE_URL`, so a role
can run a repository's database tests instead of skipping them. The sidecar
SHALL run without root, without capabilities and without privilege
escalation, and its data SHALL NOT outlive the pod.

#### Scenario: The worker starts once the database answers

- **WHEN** a worker Job starts
- **THEN** the worker container starts only after the sidecar's
  `pg_isready` probe succeeds
- **AND** a connection to `HABITAT_TEST_DATABASE_URL` succeeds

#### Scenario: Nothing survives the run

- **WHEN** the worker container ends
- **THEN** the sidecar stops and its `emptyDir` is removed with the pod
