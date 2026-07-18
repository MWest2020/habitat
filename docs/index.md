---
status: draft
last_reviewed: 2026-07-18
---

# Habitat — documentatie

Habitat is een minimaal platform waarop Claude Code-agents als Kubernetes-Jobs
autonoom aan andere repositories werken, binnen harde grenzen: **werkverdeling ·
executie · isolatie · escalatie · audit**. Het platform weet níets van
domeinlogica. Status: kern (worker-image, kooi, dispatch, audit, orchestrator-
mandaat) is gebouwd en live getest; zie [README](../README.md) voor het overzicht
en [openspec/](../openspec/) voor de changes.

## Secties

- [reference/](reference/) — feiten: het [dispatch-contract](reference/dispatch.md).
- [explanation/](explanation/) — waarom-besluiten: de
  [architectuur](explanation/architecture.md).

Assets: [audit-dashboard.html](audit-dashboard.html) (gegenereerd run-overzicht).
