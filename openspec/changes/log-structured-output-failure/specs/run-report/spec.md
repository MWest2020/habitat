## ADDED Requirements

### Requirement: A rejected structured output is explained in the job log

When a role run ends with subtype `error_max_structured_output_retries`, the
worker SHALL write the tail of the agent's last answer (at most 2000
characters) to the job log, after the secret scan and with the same secret
patterns redacted. The run SHALL still fail closed.

#### Scenario: A builder whose verdict never matched the schema

- **WHEN** a builder run ends with `error_max_structured_output_retries`
- **THEN** the job log shows the end of its last answer, with any secret
  pattern replaced by `[REDACTED]`, and the run's verdict is `failed`
