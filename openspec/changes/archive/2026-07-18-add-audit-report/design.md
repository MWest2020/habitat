# Design — audit + run-rapport

## Stroom (in de worker, na `claude -p`)

```
agent-edits → git add -A (stage) → habitat_report.py:
   diff = git diff --cached           → diff_hash = sha256(diff)
   prev = laatste entry_hash uit .habitat/audit.jsonl (of "")
   payload = prev|ts|rol|change|run_id|verdict|subtype|diff_hash|cost|turns
   entry_hash = sha256(payload)       → append regel aan .habitat/audit.jsonl
   schrijf run-report.json + .habitat/run-report-<run_id>.html
→ git add -A → commit → push (audit + rapport reizen mee de branch in)
```

## Beslissingen

### Pipe-payload i.p.v. canonieke JSON voor de keten (clevere valkuil)
De hashketen hasht een simpele, ondubbelzinnige pipe-string van de velden, niet een
gecanonicaliseerd JSON-object. Reden: de browser moet exact dezelfde hash kunnen
herberekenen; JSON-canonicalisatie (sleutelvolgorde, float-representatie, int vs
float) verschilt subtiel tussen Python en JS en zou de in-browser-verificatie
onbetrouwbaar maken. Cost/turns gaan als hun ruwe string-vorm de payload in.

### Zelfverifiërend HTML-rapport, geen CDN
Het rapport bevat de keten als data + vanilla JS die per schakel
`sha256(prev | velden)` herberekent met `crypto.subtle.digest` en ✓/✗ toont. Alles
inline (systeemfonts, geen externe requests) — past bij een default-deny-omgeving en
is los te openen, jaren later.

### Python stdlib-only, in het image gebakken
Past bij Marks Python-conventie en is leesbaar/auditeerbaar. Stdlib-only ⇒ geen
runtime-`uv`/egress nodig. De clevere valkuil ware het in Node te doen (al aanwezig),
maar Python leest hier prettiger en `python3` toevoegen aan het image is goedkoop.

### diff_hash over gestagede agent-wijziging, vóór rapport-bestanden
`git add -A` staget de agent-edits (incl. nieuwe bestanden); `git diff --cached`
levert de volledige agent-wijziging. Het rapport-tool draait dáárna, zodat de
diff-hash de code beschrijft en niet zichzelf.

## Ketening over branches (v1)
Builder/reviewer/security draaien op aparte branches, elk geketend vanaf de tip van
`main`'s `audit.jsonl`. Bij merge kunnen de ketens samenkomen; een merge-tijd
her-ketening is een v1-verfijning. v0: één entry per run, geketend vanaf de kloon.

## Verificatie (DoD)
Lokaal: unit-achtige run van het tool in een tmp git-repo → `audit.jsonl` groeit
geketend, HTML opent en verifieert ✓. Cluster: een echte builder-run laat
`.habitat/audit.jsonl` + `.habitat/run-report-<id>.html` op de branch achter.
