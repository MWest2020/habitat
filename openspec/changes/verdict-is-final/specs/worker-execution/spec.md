## ADDED Requirements

### Requirement: The role knows its structured answer is final

The role prompt SHALL tell the role that its structured answer is its final
verdict, ends the run, is given exactly once at the end, and is never a
trial call, because under `--json-schema` the first structured answer is the
one the chain reads.

#### Scenario: A role does not try out the schema

- **WHEN** a role runs under `--json-schema`
- **THEN** its prompt states that the structured answer is final and must not
  be a trial call
