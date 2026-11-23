## ADDED Requirements

### Requirement: Who pays for a worker

Dispatch SHALL run a worker on the subscription by default, and with
`HABITAT_AUTH=api` on the API key from Secret `habitat-api-key`, in which case
the worker SHALL have neither the setup-token nor the subscription
credentials, so it cannot fall back to the subscription. Any other value
SHALL stop the dispatch.

#### Scenario: An api-mode worker runs on the key

- **WHEN** a Job is dispatched with `HABITAT_AUTH=api`
- **THEN** the worker's `ANTHROPIC_API_KEY` comes from `habitat-api-key`
- **AND** it has no `CLAUDE_CODE_OAUTH_TOKEN` and no mounted credentials

#### Scenario: The default is unchanged

- **WHEN** a Job is dispatched without `HABITAT_AUTH`
- **THEN** it uses the setup-token and the optional credentials, as before
