## ADDED Requirements

### Requirement: A browser for the playtester

The worker image SHALL contain a pinned Python Playwright with its Chromium
headless shell and the `playtest-shoot` command, so the playtester can serve and
open an app without network access.

#### Scenario: playtest-shoot in the cage

- **WHEN** the playtester runs `playtest-shoot --serve-dir web`
- **THEN** screenshots appear in `/work/playtest/` and the command prints a JSON summary
