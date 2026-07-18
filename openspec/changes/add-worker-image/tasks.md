## 1. Containerfile

- [x] 1.1 Base-image gepind (`node:22.11.0-bookworm-slim`), nooit `latest`
- [x] 1.2 `git` + `uv` (gepind via COPY uit `ghcr.io/astral-sh/uv:0.11.15`) + Claude Code (`@anthropic-ai/claude-code@2.1.201`) + `jq`
- [x] 1.3 SPDX-header + non-root user (`worker`, uid 10001), `/work` schrijfbaar
- [x] 1.4 `entrypoint.sh` als ENTRYPOINT

## 2. entrypoint.sh (≤200 regels)

- [x] 2.1 Valideer verplichte env; faal vroeg en leesbaar bij ontbreken
- [x] 2.2 Git credential-helper leest PAT uit env — niet in URL/reflog/config
- [x] 2.3 Clone `HABITAT_REPO` over HTTPS (owner/repo, volledige URL of pad)
- [x] 2.4 Draai `claude -p --output-format json --permission-mode bypassPermissions --max-budget-usd`
- [x] 2.5 Verdict uit JSON via `if .is_error == false` (niet `// true` — jq-valkuil), niet uit exit-code
- [x] 2.6 Schrijf `run-report.json` (rol, change, run-id, verdict, `total_cost_usd`, turns, exit, timestamp)
- [x] 2.7 Commit + push branch `habitat/<rol>/<change>` incl. `run-report.json`; nooit `main`

## 3. GitHub Actions build → GHCR

- [x] 3.1 Workflow `.github/workflows/worker-image.yml`, trigger op `worker/**`-wijziging
- [x] 3.2 Build + push naar `ghcr.io/mwest2020/habitat-worker:${{ github.sha }}`, geen `latest`
- [x] 3.3a CI-run groen (runs 29125972393 en 29205144402, success, 2026-07-11/12; geverifieerd 2026-07-18)
- [ ] 3.3b package-zichtbaarheid op publiek: kan alléén via de GitHub-UI (de packages-REST-API
      kent geen visibility-wijziging) — Mark: package settings → Danger Zone → Change visibility.
      Tot die tijd werkt het `ghcr-pull`-pull-secret (bewezen in de live run).

## 4. Verificatie (DoD)

- [x] 4.1 Lokale smoke: image gebouwd, tools aanwezig, non-root (laag 1)
- [x] 4.2 Echt `claude -p --output-format json` levert `is_error`/`total_cost_usd`/`num_turns`; `--max-budget-usd` werkt (laag 2)
- [x] 4.3 PAT-over-HTTPS clone van private repo in-container; PAT niet gelekt (laag 3a)
- [x] 4.4 Volledige entrypoint end-to-end: branch + `run-report.json` gepusht, verdict correct (laag 3b)
- [x] 4.5 Échte end-to-end op GitHub-testrepo met echte `claude -p` in een K8s-Job — GROEN (verdict=ok, branch + run-report gepusht)
