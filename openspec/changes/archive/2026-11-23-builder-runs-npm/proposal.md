# The builder can install and test a Node project

## Why

2026-10-24, convergence `fundament` (convergence#7): the builder wrote four
`package.json`s and their tests and ran none of them. Its allow list has
`npm ci`, `npm test *` and `bash verify.sh`, but not `npm install`, so it
could not write a `package-lock.json`, and without one `npm ci` fails. It
read the failures as a sandbox that refuses all code and reported every test
as unrun; the reviewer failed the change for exactly that. Reproduced in a
worker pod: `bash verify.sh` is allowed; `npm install` and `node --test` are
refused.

## What changes

`worker/settings/builder.json` allows `npm install`, `npm install *`,
`npm test` and `node --test` / `node --test *`. The risk is the one `make *`
and `uv run *` already carry, running the repository's own code inside the
container, plus the dependencies' install scripts; the container and its
egress policy stay the boundary. A new worker image follows; ratatoskr pins it.
