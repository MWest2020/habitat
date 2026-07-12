---
status: draft
last_reviewed: 2026-07-12
---

# Habitat — documentatie

Habitat is een minimaal platform waarop Claude Code-agents autonoom aan andere
repositories werken binnen harde, niet-onderhandelbare grenzen; het levert vijf
dingen — **werkverdeling · executie · isolatie · escalatie · audit** — en weet
níets van domeinlogica. Deze `docs/`-map volgt het handbook-docs-contract; de
canonieke inleiding blijft de [README](../README.md).

**Status**: in opbouw (v0). Gemigreerde pagina's staan op `status: draft` tot een
echte review ze op `current` zet.

## Secties

- **Uitleg** — [`explanation/architecture.md`](explanation/architecture.md): waarom
  Habitat zo gebouwd is (kooi, escalatiematrix, rollback, levensloop van een run).
- **Referentie** — [`reference/dispatch.md`](reference/dispatch.md): het
  dispatch-contract (`dispatch.sh <rol> <change> <repo>`, env-variabelen, branch- en
  run-report-conventies).

De formele specificatie staat per change onder
[`openspec/changes/`](../openspec/changes/).
