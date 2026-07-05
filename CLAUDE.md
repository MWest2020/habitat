# Werken in de Habitat-repo

Dit is het conventie-bestand voor wie in *deze* repo (`MWest2020/habitat`) werkt.
Het *orchestrator-mandaat* (escalatiematrix, verboden paden voor draaiende agents)
is iets anders en leeft in `orchestrator/CLAUDE.md` (change `add-orchestrator`).

## Wat Habitat is

Een minimaal platform: werkverdeling, executie, isolatie, escalatie, audit voor
Claude Code-agents die als K8s Jobs op een thuiscluster aan andere repo's werken.
Habitat weet níets van domeinlogica. Zie `README.md`.

## Werkwijze

- **OpenSpec-flow**: conversational design → `propose` → `apply` → `archive`.
  Geen code vóór een change op "apply" staat. Changes onder `openspec/changes/`.
- **Saai en auditeerbaar boven snel of slim.** Benoem de "clevere valkuil" waar
  relevant. Alles wat een agent doet moet reconstrueerbaar zijn uit git + audit-JSONL.

## Conventies

- **Python via `uv`, nooit `pip`.**
- **Bestanden ≤ 200 regels.**
- **Secrets**: nooit hardcoded, nooit client-side, alleen SOPS+age. Nooit een
  gedecrypt secret committen.
- **Immutable images**: getagd per commit-SHA, nooit `latest`.
- **Licentie**: EUPL-1.2. Nieuwe bronbestanden krijgen een SPDX-header:
  `# SPDX-License-Identifier: EUPL-1.2`.
- **Commits blijven lokaal tot Mark pusht.**

## Verboden paden (hard-fail)

Agents verbouwen hun eigen kooi niet. Wijzigingen aan `CLAUDE.md`, `.claude/agents/`,
NetworkPolicies, RBAC of Job-templates zijn verboden en niet-escaleerbaar.
