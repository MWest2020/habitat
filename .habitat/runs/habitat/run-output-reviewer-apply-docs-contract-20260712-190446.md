# Habitat reviewer — apply-docs-contract

_run_id reviewer-apply-docs-contract-20260712-190446 · verdict ok · 2026-07-12T19:06:07Z_

---

All checks complete. Here is my verdict.

---

## Reviewer-verdict: **PASS** — change `apply-docs-contract`

Diff beoordeeld: `main...HEAD` (commits `ab24ad0` docs + `30a7954` run-artefacten).

### 1. Scope ✓
- Docs-werk (`docs/architecture.md` → stub, nieuwe `docs/explanation/architecture.md`, `docs/index.md`, `docs/reference/dispatch.md`) + `tasks.md`-vinkjes binnen de change-map.
- `.mcp.json` (taak 2.4) was al geseed in `21fb2c1` en zit dus in `main`; inhoud volgt het template met placeholder `TODO-change-3` — correct, geen diff nodig, geen echte handbook-URL gelekt.
- Run-artefacten (`.habitat/audit.jsonl`, `run-report.json`, HTML/MD-run-report) zijn de standaard audit-output van de builder-Job, niet buiten-scope docs-wijzigingen.
- Taak 4.1 (push + PR) terecht **níet** uitgevoerd — respecteert CLAUDE.md "Commits blijven lokaal tot Mark pusht".

### 2. Contract ✓
- Markdown alleen in toegestane locaties: `index.md`, `explanation/`, `reference/` — plus de door de proposal **expliciet gevraagde** redirect-stub op de oude plek (`docs/architecture.md`, `status: deprecated`). `docs/audit-dashboard.html` blijft als asset staan (geen markdown).
- Elke pagina heeft front matter met `status` + `last_reviewed: 2026-07-12`. Gemigreerde/nieuwe pagina's op `status: draft`, stub op `deprecated` — conform.
- **Geen** `owner`-veld (de `owner`-treffers zijn `owner/repo`, `CODEOWNERS` en de zelfcheck-tekst, geen front-matter-veld).
- Eén taal (Nederlands). Relatieve links kloppen na de verplaatsing (`../../openspec/changes/` vanuit `explanation/`, `../README.md` vanuit `docs/`).

### 3. Kooi intact ✓
`CLAUDE.md`, `.claude/agents/` en CI-config zijn níet geraakt.

### 4. Geen secrets ✓
Secret-scan over de volledige diff schoon; audit/run-report bevatten alleen hashes, kosten en metadata — geen tokens, credentials of secret-URLs.

**Aanbeveling:** klaar voor Mark om te mergen. Geen fixes vereist.
