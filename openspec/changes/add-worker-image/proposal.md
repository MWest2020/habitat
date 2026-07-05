## Why

Zonder een worker-image valt er niets uit te voeren en dus niets te testen. De
worker is de enige plek waar een Claude Code-agent daadwerkelijk draait: één
container die een doelrepo clonet, `claude -p` in een rol draait, en het resultaat
als branch teruggeeft. Alles wat daarna komt (kooi, dispatch, audit) hangt aan dit
contract. Deze change legt dat contract vast: wat gaat erin (env), wat komt eruit
(branch + rapport), en hoe de image reproduceerbaar en immutable wordt gebouwd.

## What Changes

- **Containerfile** met gepinde versies van base, `git`, `uv` en Claude Code
  headless. Nooit `latest`. Alleen de worker-eigen tools worden gebakken;
  doel-repo-deps worden runtime geïnstalleerd (via de proxy uit `add-cage`).
- **entrypoint** dat env leest (`HABITAT_REPO`, `HABITAT_ROLE`, `HABITAT_CHANGE`,
  `HABITAT_RUN_ID`), de doelrepo over HTTPS clonet met een single-repo
  fine-grained PAT, `claude -p --output-format json --max-turns N` draait, succes
  bepaalt uit de JSON (`is_error`/`subtype`) en niet uit de exit-code, de branch
  `habitat/<rol>/<change>` pusht en een `run-report.json` mee de branch in schrijft.
- **GitHub Actions-workflow** die de image bouwt en naar GHCR pusht, publiek,
  getagd per commit-SHA, nooit `latest`.

## Capabilities

### New Capabilities

- `worker-execution`: het runtime-contract van één worker-Job — welke env erin
  gaat, hoe geclonet/gepusht wordt, hoe `claude -p` wordt aangeroepen, hoe succes
  wordt bepaald, en wat er als output achterblijft (branch + `run-report.json`).
- `worker-image-build`: hoe de image reproduceerbaar en immutable wordt gebouwd en
  gepubliceerd (gepinde Containerfile, GitHub Actions, GHCR publiek, SHA-tag).

### Modified Capabilities

<!-- Geen: dit is een van de eerste changes; er bestaan nog geen specs. -->

## Impact

- Introduceert het image `ghcr.io/mwest2020/habitat-worker` en de env-interface
  waarop `add-dispatch` de Job-manifests bouwt.
- Legt de PAT-over-HTTPS-git-auth en de proxy-afhankelijkheid vast die `add-cage`
  moet leveren; de worker draait pas volwaardig binnen de kooi.
- Bepaalt waar `total_cost_usd` en het run-verdict vandaan komen, wat `add-audit-report`
  consumeert.
