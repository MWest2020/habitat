# Tasks

- [x] `dispatch/dispatch.sh` and `dispatch/job-template.yaml`: `HABITAT_AUTH`,
      three Secret names per mode. Proof: both modes render as intended.
- [x] Secret `habitat-api-key` in namespace `agents`, from ratatoskr's SOPS
      secret. Proof: a probe Job in api mode reported
      `apiKeySource: ANTHROPIC_API_KEY` with no setup-token in its env.
- [x] `docs/reference/dispatch.md`: the two modes.
- [ ] Live: the first convergence chain runs in api mode.
