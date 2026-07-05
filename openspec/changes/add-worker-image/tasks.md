## 1. Containerfile

- [ ] 1.1 Kies en pin een base-image (expliciete digest of versie-tag, nooit `latest`)
- [ ] 1.2 Installeer `git` + `uv` (gepind) en Claude Code headless (gepinde versie)
- [ ] 1.3 SPDX-header + minimale, non-root user; geen doel-repo-deps bakken
- [ ] 1.4 Zet `entrypoint.sh` als ENTRYPOINT

## 2. entrypoint.sh (≤200 regels)

- [ ] 2.1 Valideer verplichte env; faal vroeg en leesbaar bij ontbreken
- [ ] 2.2 Configureer git credential zó dat de PAT niet in URL/reflog/logs lekt
- [ ] 2.3 Clone `HABITAT_REPO` over HTTPS via `HTTPS_PROXY`
- [ ] 2.4 Draai `claude -p "<rol>" --output-format json --max-turns N` met `ANTHROPIC_API_KEY`
- [ ] 2.5 Bepaal verdict uit JSON `is_error`/`subtype` (defensieve parser), niet uit exit-code
- [ ] 2.6 Schrijf `run-report.json` (rol, change, run-id, verdict, `total_cost_usd`, turns, timestamps)
- [ ] 2.7 Commit + push branch `habitat/<rol>/<change>` incl. `run-report.json`; push nooit `main`

## 3. GitHub Actions build → GHCR

- [ ] 3.1 Workflow `.github/workflows/worker-image.yml`, trigger op Containerfile/entrypoint-wijziging
- [ ] 3.2 Build + push naar `ghcr.io/mwest2020/habitat-worker:${{ github.sha }}`, publiek
- [ ] 3.3 Bevestig dat er geen `latest`-tag wordt gepubliceerd

## 4. Verificatie (DoD)

- [ ] 4.1 Lokale rook-test: `docker run` met de env-set + test-PAT tegen een testrepo
- [ ] 4.2 Bevestig: branch gepusht, `run-report.json` aanwezig, PAT nergens gelekt
- [ ] 4.3 Bevestig: image op GHCR per SHA getagd en herleidbaar naar de commit
