# reproducible-diff-hash

## Why

`habitat_report.py` berekent `diff_hash = sha256(git diff <base-ref>)` op
report-tijd — vóór de habitat-artefacten (`.habitat/audit.jsonl`, het HTML-
rapport, `run-report.json`, later `run-output-*.md`) gecommit worden. De
gepushte branch bevat die artefacten wél. Gevolg: een auditor die
`git diff <base-ref> HEAD` op de branch draait ziet **6** bestanden en krijgt een
andere hash dan de opgeslagen `diff_hash` (die **2** code-bestanden dekt). De
diff_hash is dus niet reproduceerbaar vanaf de branch — precies het punt van de
audit-keten. Gesignaleerd door de reviewer bij een livetest ("rapport meldt 2
bestanden, commit bevat 6").

## What Changes

- **`report/habitat_report.py`**: de diff (en `--stat`) sluiten de habitat-
  artefacten expliciet uit via pathspec `-- . ':(exclude).habitat'
  ':(exclude)run-report.json'`. Daardoor dekt `diff_hash` uitsluitend de
  agent-codewijziging en is hij reproduceerbaar vanaf de branch (`git diff
  <base> HEAD` mét dezelfde exclusies levert dezelfde hash). De **waarde
  verandert niet** t.o.v. nu (op report-tijd bestonden die artefacten nog niet),
  dus bestaande audit-ketens blijven geldig.
- `run-report.json` krijgt een `diff_hash_scope`-veld dat het reproductie-
  commando documenteert (buiten de gehashte auditvelden, geen ketenbreuk).
- Test `report/test_habitat_report.py`: bewijst reproduceerbaarheid vanaf de
  branch en dat de artefacten anders wél zouden meetellen.

## Impact

- Wijziging onder `report/**` (in de worker-image gebakken) → nieuwe image
  nodig. Geen contractbreuk: `diff_hash`-waarden en de hashketen blijven gelijk;
  alleen reproduceerbaarheid + één documentatieveld erbij.
