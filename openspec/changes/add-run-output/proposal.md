## Why

Een run laat nu wél metadata op de branch achter (`run-report.json`,
`.habitat/audit.jsonl`, `.habitat/run-report-<run_id>.html`), maar **niet** de
inhoudelijke uitvoer van de agent. Voor een reviewer- of security-run is dat juist
het waardevolle deel: de bevindingen. Die tekst staat alleen in het `.result`-veld
van de `claude -p`-JSON in de pod, en die pod wordt na de Job verwijderd — dus de
review is achteraf niet terug te vinden op GitHub. Reconstrueerbaarheid uit git is de
kern van het platform; dit gat dicht dat voor de reviews.

## What Changes

- **`worker/entrypoint.sh`**: na `habitat_report.py` (dus ná de diff-hash-berekening)
  schrijft de worker het `.result`-veld uit `claude-output.json` naar
  `.habitat/run-output-<run_id>.md` en commit dat mee op de branch. Bewust ná het
  rapport, zodat de code-diff-hash niet vervuild raakt — net als `run-report.json` is
  dit een habitat-artefact, geen agent-codewijziging. Een `jq -e 'has("result")'`-guard
  slaat het over bij een gecrashte/niet-parseerbare run.

## Capabilities

### Modified Capabilities

- `worker-execution`: het "duurzaam run-rapport"-contract wordt uitgebreid — naast
  `run-report.json` bewaart de worker ook de agent-eind-uitvoer als markdown, zodat
  reviews/bevindingen de opruiming van de pod overleven.

## Impact

- Elke run met een `result` laat nu extra `.habitat/run-output-<run_id>.md` op de
  branch achter.
- Wijziging in `worker/**` → nieuwe worker-image nodig (CI tagt per commit-SHA);
  daarna de `WORKER_IMAGE`-pin bij de volgende dispatch bijwerken.
- Geen contractbreuk: bestaande artefacten en de audit-hashketen blijven ongewijzigd.
