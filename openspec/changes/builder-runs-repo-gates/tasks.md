# Tasks

- [x] `worker/settings/builder.json`: the five entries, nothing else.
- [x] Validate the JSON; `openspec validate builder-runs-repo-gates --strict`.
- [x] Push. The worker-image workflow built `e01d0692e738…`.
- [x] ratatoskr `agents/factory.yml`: pin the new image.
- [ ] Live: the next chat-started build on ratatoskr shows the builder running
      `bash verify.sh` in its run output.
