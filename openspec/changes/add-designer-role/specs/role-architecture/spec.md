## ADDED Requirements

### Requirement: A designer role delivers a checked brand proposal

The worker SHALL accept a `designer` role that reads a brief from
`HABITAT_TASK_REF`, writes its delivery under `design/brand/` in the target
repository, and may only use Read, Edit, Write, Grep, Glob, scoped git
commands, `design-kit`, `design-check`, `logo-tool` and `playtest-shoot`;
network tools and `git push` SHALL be denied. The run SHALL pass only when the
role's structured verdict is PASS **and** `design-check design/brand`, run by
the entrypoint from the image after the agent finished, exits 0.

#### Scenario: A delivery that fails a gate

- **WHEN** the designer answers PASS but its adaptive foreground has art outside the 66 dp safe circle
- **THEN** the entrypoint's `design-check` fails, the run verdict is `failed` and the Job fails

#### Scenario: A complete delivery

- **WHEN** every required file exists and every gate passes and the verdict is PASS
- **THEN** the branch with `design/brand/` is pushed and `designer.sh` opens a draft PR
