## 1. Rapport-tool (Python stdlib)

- [x] 1.1 `report/habitat_report.py`: args (rol/change/run-id/verdict/subtype/cost/turns/exit/repo)
- [x] 1.2 diff_hash = sha256 van `git diff --cached`; diff-stat voor de samenvatting
- [x] 1.3 hash-chain: lees laatste `entry_hash`, schrijf nieuwe regel naar `.habitat/audit.jsonl`
- [x] 1.4 schrijf `run-report.json` (compat) + `.habitat/run-report-<run_id>.html`
- [x] 1.5 HTML: single file, systeemfonts, geen CDN, vanilla-JS keten-verificatie (`crypto.subtle`)

## 2. Worker-integratie

- [x] 2.1 `python3` in de Containerfile; `report/` in het image gebakken
- [x] 2.2 entrypoint: `git add -A` → rapport-tool → `git add -A` → commit → push
- [x] 2.3 inline `run-report.json`-generatie vervangen door het tool

## 3. Verificatie (DoD)

- [x] 3.1 Lokaal in een tmp git-repo: keten groeit correct; manipulatie → ✗ in HTML
- [x] 3.2 Cluster-run: `.habitat/audit.jsonl` + `run-report-<id>.html` op de branch
- [x] 3.3 HTML opent offline en verifieert de keten (✓)
