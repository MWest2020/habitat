# harden-run-artifacts

## Why

Twee lage-maar-reële residuen uit de security-review van `reproducible-diff-hash`
(round 3, N1 + N3):

- **N1 — `run-output-<run_id>.md` wordt alleen voorwaardelijk geschreven.**
  `worker/entrypoint.sh` schrijft dit artefact alleen als het `claude -p`-JSON
  een `result`-veld heeft (`jq -e 'has("result")'`). Ontbreekt dat (zeldzaam,
  bv. een gecrashte envelope), dan blijft een dóór de agent vooraf geschreven
  `.habitat/run-output-<run_id>.md` op de branch staan — en die valt buiten de
  `diff_hash` (per exacte naam uitgesloten). Een smal smokkelkanaal én een gat in
  de bewijsketen (soms geen run-output). De spec (`worker-execution`) schrijft dit
  overslaan nu zelfs voor.

- **N3 — een beschadigde `.habitat/audit.jsonl` liet `habitat_report.py` crashen.**
  `build_entry` deed `json.loads(lines[-1])` zonder vangnet; een door de agent
  bedorven laatste regel wierp `JSONDecodeError` en brak het rapport af. De fix
  (fail-closed: `prev_hash=""` bij een kapotte regel, keten breekt zichtbaar)
  landde al inline in `reproducible-diff-hash`, maar zonder eigen change, test of
  spec. Deze change formaliseert en test dat gedrag.

## What Changes

- **`report/habitat_report.py`**: het schrijven van `.habitat/run-output-<run_id>.md`
  verhuist van de shell naar dit ene, testbare artefact-module en gebeurt
  **onvoorwaardelijk**. Nieuw `--output-file` (pad naar het `claude -p`-JSON):
  bij een leesbaar `result` komt die tekst in de markdown, anders een placeholder.
  Zo bezit habitat dit bestand deterministisch en kan een agent er geen eigen
  versie voor smokkelen. Het bestand wordt ná de diff-hash geschreven en is per
  exacte naam uitgesloten, dus de hash-waarde blijft gelijk.
- **`worker/entrypoint.sh`**: geeft `--output-file "$OUT"` door en laat het
  voorwaardelijke 6b-`jq`-blok vallen (nu in Python, altijd geschreven).
- **`report/habitat_report.py`**: de fail-closed audit-parse (N3) blijft; er komt
  testdekking op (kapotte laatste regel → geen crash, `prev_hash` leeg).
- **Spec-delta's**: `worker-execution` (run-output altijd geschreven, ook zonder
  `result`) en `audit-trail` (beschadigde audit-regel is fail-closed).

## Impact

- Wijziging onder `report/**` + `worker/**` (in de worker-image gebakken) →
  nieuwe image nodig. Geen contractbreuk voor de `diff_hash`-waarde of de
  hashketen; alleen sterker gedrag: run-output altijd aanwezig en
  habitat-eigendom, audit-parse crasht niet meer op sabotage.
