## ADDED Requirements

### Requirement: A role's branch push retries before the role fails

The worker SHALL push a role's branch up to four times, with increasing waits between attempts, and SHALL fail the role on the push only when every attempt has failed. Each failed attempt SHALL be logged with its exit code. A retried push SHALL never be a force push.

#### Scenario: A transient push error

- **WHEN** the first push of a role's branch is rejected by the remote and a later attempt succeeds
- **THEN** the role's result stands and the log shows the failed attempts and the success

#### Scenario: The push keeps failing

- **WHEN** every push attempt fails
- **THEN** the role fails as it does today, after the last attempt
