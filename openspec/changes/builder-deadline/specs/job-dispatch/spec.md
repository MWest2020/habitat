## ADDED Requirements

### Requirement: Deadline per role

Without an explicit `ACTIVE_DEADLINE_SECONDS`, dispatch SHALL give a builder
Job an `activeDeadlineSeconds` of 3600 and every other role 1800, because a
builder runs the repository's tests, its database tests included, and the
other roles read and judge.

#### Scenario: A builder gets an hour

- **WHEN** a builder Job is dispatched without `ACTIVE_DEADLINE_SECONDS`
- **THEN** its `activeDeadlineSeconds` is 3600

#### Scenario: Other roles keep 30 minutes

- **WHEN** an architect, reviewer or security Job is dispatched without
  `ACTIVE_DEADLINE_SECONDS`
- **THEN** its `activeDeadlineSeconds` is 1800
