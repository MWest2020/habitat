# The builder runs the repository's own gate

## Why

On 2026-10-22 the first chat-started build (ratatoskr `retire-bridge`,
ratatoskr#157) passed all four roles, but the builder left its last task open:

> `bash verify.sh` is green ... **Not run**: this sandbox denies `bash
> verify.sh` (and any `python3 scripts/...` invocation) outright, so a human or
> CI must confirm.

CI caught up that time. But a builder that cannot run the repository's gate
hands in work it could not test. The reviewer then judges a diff that was never
run, and the first proof of correctness comes after the PR is open. The
builder's allowlist has `make *`, `pytest *`, `uv run *` and `npm run *`, all
commands that execute repository code. It lacks the two entry points
ratatoskr-style repositories use: `bash verify.sh` and `python3 -m unittest`.

## What changes

`worker/settings/builder.json` allows, and nothing broader:

- `Bash(bash verify.sh)` and `Bash(./verify.sh)`;
- `Bash(python3 -m unittest)` and `Bash(python3 -m unittest *)`;
- `Bash(python3 -m pytest *)`.

Free `bash *` or `python3 *` stays out. Those would make every other entry on
the deny list decorative, because `python3 -c` reads anything the container can
read. The risk of the new entries is the risk `make *` already carries: running
the repository's own code inside the container, which stays the outer boundary.
The guard hook and the deny list (push, secrets, network tools) are unchanged.

A new worker image follows from the push to `worker/`; ratatoskr's
`agents/factory.yml` pins it.
