# A role that fails its structured answer runs once more

## Why

2026-10-24: three chains stopped on `error_max_structured_output_retries`
(demo-core's architect, gdd-economy's reviewer, demo-slice's security after
architect, builder and reviewer had passed). That is a model failing to fit
its answer into the schema, not a verdict on the change; stopping the chain on
it throws away the work of every role before it.

## What changes

`dispatch/chain.sh` runs a role once more when its run ended on
`error_max_structured_output_retries`, and only then. Any other failure stops
the chain as before. Cost: one extra role run (typically under $1).
