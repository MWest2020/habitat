# Tasks: harden-run-artifacts

## 1. Run-output altijd geschreven (N1)

- [x] 1.1 `report/habitat_report.py`: nieuw `--output-file`; schrijf
      `.habitat/run-output-<run_id>.md` **onvoorwaardelijk** ná de diff-hash —
      met `result` uit het JSON, anders een placeholder. Robuust tegen
      ontbrekend/onparseerbaar/niet-object JSON (`agent_result`).
- [x] 1.2 `worker/entrypoint.sh`: geef `--output-file "$OUT"` door; verwijder het
      voorwaardelijke 6b-`jq`-blok (run-output nu in Python, altijd).

## 2. Fail-closed audit-parse (N3)

- [x] 2.1 `report/habitat_report.py`: `try/except` rond `json.loads(lines[-1])`
      (`prev_hash=""` bij kapotte regel — fail-closed). Bovendien toont de
      HTML-render onleesbare/niet-object regels als expliciet gebroken rij i.p.v.
      ze stil weg te laten (security-review F1).

## 3. Tests

- [x] 3.1 `report/test_habitat_report.py`: run-output altijd geschreven —
      (a) met `result`, (b) zonder `--output-file`/zonder `result` → placeholder,
      (c) een vooraf door de "agent" geschreven `run-output-<id>.md` wordt
      geklobberd (habitat bezit het bestand); en het valt buiten `diff_hash`.
      Plus `agent_result` robuustheid (ontbrekend/onleesbaar/niet-object/niet-string).
- [x] 3.2 `report/test_habitat_report.py`: kapotte laatste `audit.jsonl`-regel →
      `build_entry` crasht niet, `prev_hash` leeg; en alle bedorven regels blijven
      als gebroken rij zichtbaar in het HTML-rapport (F1).

## 4. Spec

- [x] 4.1 Spec-delta `worker-execution`: run-output altijd geschreven (ook zonder
      `result`, dan placeholder), habitat-eigendom, geen smokkelkanaal.
- [x] 4.2 Spec-delta `audit-trail`: beschadigde audit-regel is fail-closed
      (geen crash, keten breekt zichtbaar) en onleesbare regels blijven zichtbaar.

## 5. Verify

- [x] 5.1 `python3 report/test_habitat_report.py` groen; shellcheck op
      `worker/entrypoint.sh` clean; py-syntax ok; `openspec validate`.
- [x] 5.2 Code-review reviewer + security in verse context; beide PASS.
      Security-F1 (onleesbare regels stil weggelaten) verwerkt.
- [ ] 5.3 Nieuwe image; cluster-sanity: een run → `.habitat/run-output-<id>.md`
      aanwezig en habitat-geschreven; `diff_hash` blijft reproduceerbaar vanaf de
      branch. Daarna afvinken/archiveren.
