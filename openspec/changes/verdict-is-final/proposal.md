# A role's structured answer is final, and the prompt says so

## Why

2026-10-24, wordsworth#221: the architect of `pilot-ingest-manifest` (which
passed the architect five times before) ended with the verdict
`{"verdict":"FAIL","summary":"Test call to isolate schema issue with the plan
field. ...","plan":[{"objective":"test","files":["a.md"],...}]}`. It called
the StructuredOutput tool to try out the schema; under `--json-schema` that
call is the answer and ends the run. The chain stopped on a verdict nobody
gave, and a build was spent on it.

## What changes

The role prompt in `worker/entrypoint.sh` says that the structured answer is
the final verdict, ends the run, is given exactly once at the end, and is
never a trial call. A new worker image follows from the push to `worker/`;
ratatoskr's `agents/factory.yml` pins it.
