## ADDED Requirements

### Requirement: The builder can install and test a Node project

The builder role SHALL be allowed to run `npm install` (with or without
package names), `npm test` and `node --test`, so that it can create a
lockfile and run a Node repository's tests itself, not hand in tests that
never ran.

#### Scenario: A new package gets a lockfile and green tests

- **WHEN** a change adds a `package.json`
- **THEN** the builder can run `npm install` to write `package-lock.json`
- **AND** run the tests with `npm test` or `node --test`
