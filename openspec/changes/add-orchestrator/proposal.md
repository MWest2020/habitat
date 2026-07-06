## Why

De worker, de kooi, de dispatch en de audit staan en zijn live bewezen. Wat
ontbreekt is de laag die het geheel bestuurt zonder zelf gevaarlijk te worden: het
mandaat van de orchestrator. Dit is de éne Claude Code-sessie op de laptop die Jobs
dispatcht, logs volgt, en bij elke grens pauzeert en Mark aanroept. Het mandaat legt
letterlijk vast wat autonoom mag, wat escaleert, en wat verboden is — zodat de
orchestrator een betrouwbare bestuurder is, geen tweede risico.

## What Changes

- **`orchestrator/CLAUDE.md`**: het mandaat van de orchestrator-sessie, met de
  escalatiematrix en de verboden paden **letterlijk**. Bevat: wat de orchestrator
  mag (Jobs CRUD in `agents`, logs/branches lezen, dispatchen via `dispatch.sh`,
  Mark aanroepen), wat hij nooit doet (zelf productiecode schrijven, mergen,
  eigen-kooi verbouwen), en de autonoom/escaleer/verboden-driedeling.
- **`orchestrator/start-tmux.sh`**: zet de tmux-indeling op — venster 0 de
  orchestrator-sessie, een statuspane (wachtrij/escalaties), en per Job een log-pane
  op afroep. Bare, geen ceremonie.

## Capabilities

### New Capabilities

- `orchestrator-mandate`: de niet-onderhandelbare gedragsregels van de
  orchestrator-sessie — de escalatiematrix en de verboden paden — waaraan de sessie
  zich houdt en waarop hij escaleert.

### Modified Capabilities

<!-- Geen: het mandaat is nieuw; het verwijst naar bestaande changes. -->

## Impact

- Sluit de v0-loop: builder → reviewer → security → escalatie van de merge naar Mark
  met een link naar het HTML-run-rapport.
- Het mandaat verwijst naar `dispatch/dispatch.sh` (change c) en het
  HTML-run-rapport (change e); de verboden paden spiegelen de kooi (change b).
- v0: geen merge-automatisering. Elke merge naar `main` escaleert naar Mark.
