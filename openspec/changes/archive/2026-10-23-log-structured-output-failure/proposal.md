# Say why a role's structured output was rejected

## Why

On 2026-10-23 the wordsworth builder for `ingest-records-source` ran 148 turns
and finished the work: twelve files, and 1022 tests pass on its branch. It
still failed, with subtype `error_max_structured_output_retries`, because its
final answer never matched `worker/schemas/builder.json`. With
`--output-format json` habitat keeps only the final envelope. The job log said
`rol-verdict=geen subtype=error_max_structured_output_retries` and nothing
more, so nobody could tell which field was wrong.

## What changes

When the subtype is `error_max_structured_output_retries`, the entrypoint
writes the tail of the agent's last answer (`.result`, at most 2000
characters) to the job log. It does so after the secret scan, and with the same
secret patterns redacted. The verdict does not change: the run still fails
closed.
