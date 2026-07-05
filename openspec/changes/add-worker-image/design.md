# Design — worker-image

## Contract in één plaatje

```
env in                          worker (K8s Job, in de kooi)                 uit
──────                          ────────────────────────────                 ───
HABITAT_REPO      ─┐   entrypoint.sh:                                ┌─ branch
HABITAT_ROLE       │   1. git clone <repo> (HTTPS + PAT, via proxy)  │   habitat/<rol>/<change>
HABITAT_CHANGE     ├─▶ 2. claude -p "<rol>" --output-format json ────┼─ run-report.json
HABITAT_RUN_ID     │      --max-turns N   (ANTHROPIC_API_KEY)        │   (in de branch)
ANTHROPIC_API_KEY ─┤   3. verdict = JSON.is_error/subtype            └─ stdout (kubectl logs)
GIT_PAT (secret)  ─┘   4. git push branch + run-report.json
```

## Beslissingen

### Succes uit de JSON, niet uit de exit-code (clevere valkuil)
`claude -p` geeft óók een non-zero exit-code bij max-turns-bereikt, stdin-overflow
en auth-fout — dus `$?` is een onbetrouwbare succesindicator. Het verdict komt uit
het JSON-eindobject: `is_error` (bool) en `subtype`. De exit-code gebruiken we
alleen als grove check "kwam er überhaupt parseerbare JSON uit". Parser is defensief:
ontbrekende velden = afwezig, nooit hard indexeren (het per-event schema van
`stream-json` is niet volledig gedocumenteerd).

### Git-auth: single-repo fine-grained PAT over HTTPS
Een deploy-key is SSH-only en SSH:22 gaat niet door de HTTP-egress-proxy uit
`add-cage`. Daarom HTTPS + een fine-grained PAT die tot één repo + `contents:write`
scoped is, geleverd via een per-node secret. Alles loopt zo door de ene proxy
(één egress-pad). De PAT komt via een git credential-mechanisme, nooit in de URL
die in reflog/logs belandt.

### Deps: alleen worker-eigen tools gebakken
Het image bakt `claude`/`uv`/`git` op gepinde versies. Doel-repo-deps (de repo kan
z'n eigen `uv sync`/`npm ci` willen) worden runtime geïnstalleerd via de proxy.
Daarom blijft de proxy-allowlist pypi+npm bevatten. De clevere valkuil zou zijn om
"alles te bakken" — dat kan niet, want de worker weet vooraf niet welke doelrepo of
toolchain er komt.

### Permission-mode: non-interactief
Headless draait de agent vast als hij op tool-approval wacht die nooit komt. Dus een
non-interactieve mode (`--permission-mode acceptEdits`, of bypass). Verantwoord
omdat de échte grens de kooi is (netpol + RBAC + wegwerp-Job), niet de tool-approval
binnen de container. Exacte modus wordt in de implementatie vastgepind en getest.

### `run-report.json` in de branch
`kubectl logs` is vluchtig (Job wordt opgeruimd via `ttlSecondsAfterFinished`).
Daarom schrijft de worker een `run-report.json` (rol, change, run-id, verdict,
`total_cost_usd`, num_turns, timestamps) mee de branch in: duurzame audit die
`add-audit-report` consumeert, los van de logstream.

## Wat deze change NIET doet
- Geen Job-manifest / `activeDeadlineSeconds` — dat is `add-dispatch`.
- Geen NetworkPolicy / proxy / secrets — dat is `add-cage`.
- Geen rol-definities — die zijn `.claude/agents/`-files in de doelrepo.

## Rook-test (DoD)
`docker run` met de vier env-vars + een test-PAT tegen een testrepo: image clonet,
draait `claude -p`, pusht een branch met `run-report.json`. Lokaal, buiten het
cluster, vóór de kooi bestaat.
