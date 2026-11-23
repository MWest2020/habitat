# A worker can run on the API credits

## Why

Mark has $100 of Anthropic API credits a month, unused, and the game
(MWest2020/convergence) is to run on them (2026-10-24). Every worker so far
authenticates with the subscription's setup-token or credentials. The
entrypoint already accepts `ANTHROPIC_API_KEY`, but only as the last
fallback: with the subscription token present it never gets there.

## What changes

`dispatch.sh` reads `HABITAT_AUTH`: `subscription` (the default, unchanged)
or `api`. In api mode the Job names the Secret `habitat-api-key` for
`ANTHROPIC_API_KEY`, and an absent Secret for the setup-token and the
credentials mount, so the worker has the key and nothing to fall back to.
ratatoskr sets `HABITAT_AUTH=api` for the repositories it bills to the
credits.
