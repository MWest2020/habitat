## Why

Een run moet achteraf reconstrueerbaar en verifieerbaar zijn — dat is de kern van
het platform. De worker produceert nu een `run-report.json`, maar er is nog geen
manipulatiebestendig audit-spoor en geen leesbaar rapport. Deze change voegt beide
toe: een append-only, hash-chained JSONL-audit (elke run gekoppeld aan de vorige) en
een zelfstandig single-file HTML-run-rapport dat naast de code in de branch staat en
zichzelf in de browser kan verifiëren.

## What Changes

- **`report/habitat_report.py`** (Python, stdlib-only): berekent de diff-hash van de
  agent-wijziging, voegt een hash-chained regel toe aan `.habitat/audit.jsonl`
  (`entry_hash = sha256(prev_hash | velden…)`), schrijft `run-report.json`, en
  genereert `.habitat/run-report-<run_id>.html`.
- **HTML-rapport**: single file, systeemfonts, geen CDN, vanilla JS. Toont
  diff-samenvatting, verdict, kosten/turns, en de audit-hashketen — met een
  in-browser verificatie via `crypto.subtle` (✓/✗ per schakel).
- **Worker-integratie**: `python3` in het image; de entrypoint stelt de agent-diff
  veilig (`git add -A`), roept het rapport-tool aan, commit + pusht de artefacten mee.

## Capabilities

### New Capabilities

- `audit-trail`: een append-only, hash-chained JSONL-log per run (rol, change,
  diff-hash, verdict, kosten, timestamps) waarmee knoeien detecteerbaar is.
- `run-report`: een zelfstandig, zelfverifiërend single-file HTML-rapport per run,
  geversioneerd naast de code.

### Modified Capabilities

<!-- add-worker-image/worker-execution: de run-report.json wordt nu door het
     rapport-tool geschreven i.p.v. inline in de entrypoint. Klein, geen contractbreuk. -->

## Impact

- Voegt `python3` toe aan de worker-image en `report/` aan de repo (in het image gebakken).
- Elke run laat nu `.habitat/audit.jsonl` + `.habitat/run-report-<run_id>.html` +
  `run-report.json` op de branch achter — "reconstrueerbaar uit git + audit-JSONL".
- Multi-rol/merge-ketening (builder+reviewer+security op aparte branches) is een v1-verfijning.
