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

- **`report/habitat_report.py`**: de diff (en `--stat`) sluiten **exact de door
  habitat gegenereerde artefacten van de run** uit — op vaste naam plus de
  dispatch-bepaalde run-id, mét `literal`-magic (géén wildcards): `-- .
  ':(exclude,literal).habitat/audit.jsonl'
  ':(exclude,literal).habitat/run-report-<run-id>.html'
  ':(exclude,literal).habitat/run-output-<run-id>.md'
  ':(exclude,literal)run-report.json'` — niet de hele `.habitat/`-map en geen
  naam-wildcard. Daardoor dekt `diff_hash` uitsluitend de agent-codewijziging en
  is hij reproduceerbaar vanaf de branch (`git diff <base> HEAD` mét dezelfde
  exclusies levert dezelfde hash), terwijl élk ander bestand dat de agent onder
  `.habitat/` schrijft — code (`.habitat/evil.py`) óf een als artefact vermomde
  naam (`.habitat/run-report-evil.html`) — **binnen de hash blijft**. Een
  map-brede exclusie (round 1) of een naam-wildcard (round 2) zou daar een
  smokkelkanaal openen; de run-id komt van dispatch, niet van de agent. De
  hash-**waarde** verandert niet voor normale runs (habitat-artefacten bestonden
  op report-tijd nog niet en worden ná de diff geschreven), dus bestaande
  audit-ketens blijven geldig.
- `run-report.json` krijgt een `diff_hash_scope`-veld dat het reproductie-
  commando documenteert (buiten de gehashte auditvelden, geen ketenbreuk).
- Test `report/test_habitat_report.py`: bewijst reproduceerbaarheid vanaf de
  branch en dat de artefacten anders wél zouden meetellen.

## Impact

- Wijziging onder `report/**` (in de worker-image gebakken) → nieuwe image
  nodig. Geen contractbreuk: `diff_hash`-waarden en de hashketen blijven gelijk;
  alleen reproduceerbaarheid + één documentatieveld erbij.
