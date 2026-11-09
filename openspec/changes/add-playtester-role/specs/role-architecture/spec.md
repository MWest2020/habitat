## ADDED Requirements

### Requirement: A playtester role looks at the result

The chain SHALL run a `playtester` role after the reviewer and before security
when the target repository has `.factory/playtest.yml` and the change touches
one of its `paths`. The role SHALL be read-only, SHALL open the app in headless
Chromium, SHALL read its own screenshots, and SHALL give PASS or FAIL in the
reviewer's schema plus a `screenshots` list. A FAIL SHALL stop the chain.

#### Scenario: A UI change in an opted-in repository

- **WHEN** a change touches `web/index.html` in a repository whose playtest config lists `web/**`
- **THEN** the chain runs the playtester between reviewer and security

#### Scenario: No opt-in

- **WHEN** the repository has no `.factory/playtest.yml`
- **THEN** the chain runs architect, builder, reviewer and security as before
