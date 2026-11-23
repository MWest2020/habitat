## ADDED Requirements

### Requirement: One retry on a failed structured answer

When a role's run ends on `error_max_structured_output_retries`, the chain
SHALL dispatch that role once more before deciding; any other failure SHALL
stop the chain as before.

#### Scenario: A structured-output hiccup does not stop the chain

- **WHEN** the security role ends on `error_max_structured_output_retries`
- **THEN** the chain dispatches security once more
- **AND** stops only if that run fails too
