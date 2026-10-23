# Tasks

- [x] `worker/entrypoint.sh`: after the secret scan, log the redacted tail of
      `.result` when the subtype is `error_max_structured_output_retries`.
- [x] The exact pipeline (jq tail, sed redaction, prefix) was run against a
      fixture envelope with that subtype and a fake `sk-ant-` token: the tail
      is logged and the token shows as `[REDACTED]`. The entrypoint as a whole
      has no harness; `bash -n` and shellcheck pass.
- [ ] Push; the worker image rebuilds; ratatoskr `agents/factory.yml` pins it.
