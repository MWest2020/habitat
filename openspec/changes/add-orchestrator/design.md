# Design — orchestrator-mandaat

## Wat dit is

Geen code die "draait", maar het **gedragscontract** van de éne Claude Code-sessie
die het platform bestuurt. De sessie leest `orchestrator/CLAUDE.md` als mandaat en
gebruikt `dispatch/dispatch.sh` als enige actuator.

```
tmux-sessie 'habitat', venster 0:
  ┌───────────────────────────┬──────────────────────────┐
  │ pane 0: orchestrator      │ pane 1: status           │
  │  claude (mandaat=CLAUDE.md)│  watch kubectl get       │
  │  → dispatch.sh <rol> ...   │  jobs,pods (wachtrij/    │
  │  → leest run-report        │  escalaties)             │
  └───────────────────────────┴──────────────────────────┘
  log-pane per Job op afroep: tmux split-window 'kubectl logs -f job/<naam>'
```

## Beslissingen

### Mandaat als CLAUDE.md, letterlijk
De escalatiematrix en de verboden paden staan wóórdelijk in `orchestrator/CLAUDE.md`,
niet geparafraseerd. De sessie kan zo niet "vergeten" waar de grens ligt. Het bestand
staat zelf op de verboden-lijst — de orchestrator wijzigt z'n eigen mandaat niet.

### Discipline is de tweede grens, niet de eerste
De harde grens blijft de kooi (egress-policy + RBAC + wegwerp-Jobs) en GitHub branch
protection. Het mandaat is de gedrags-laag daarbovenop; als de sessie zich zou
misdragen, stopt de kooi de schade alsnog.

### Geen merge-automatisering (v0)
Elke merge naar `main` escaleert naar Mark, ook na groen. Bewuste keuze: mens in de
loop op het enige onomkeerbare punt.

### Bare tmux
`start-tmux.sh` zet twee panes op en laat het bij een gedocumenteerde one-liner voor
log-panes. Geen tmuxinator/oh-my-tmux — saai en zonder afhankelijkheden.

## Wat deze change NIET doet
- Geen auto-merge, geen self-scheduling (de orchestrator geeft zichzelf geen werk).
- Geen nieuwe rechten: hij gebruikt de orchestrator-SA uit `add-cage` (Jobs + logs).

## Verificatie (DoD)
- `bash -n` op `start-tmux.sh`; een structurele testrun (met een dummy-commando
  i.p.v. `claude`) toont twee panes en ruimt op.
- `orchestrator/CLAUDE.md` bevat de escalatiematrix + verboden paden letterlijk.
