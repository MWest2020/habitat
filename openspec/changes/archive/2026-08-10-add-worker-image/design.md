# Design — worker-image

## Contract in één plaatje

```
env in                          worker (K8s Job, in de kooi)                 uit
──────                          ────────────────────────────                 ───
HABITAT_REPO      ─┐   entrypoint.sh:                                ┌─ branch
HABITAT_ROLE       │   1. git clone <repo> (HTTPS + PAT)             │   habitat/<rol>/<change>
HABITAT_CHANGE     ├─▶ 2. claude -p "<rol>" --output-format json ────┼─ run-report.json
HABITAT_RUN_ID     │      --max-budget-usd <cap>                     │   (in de branch)
GIT_PAT (secret)   │   3. verdict = JSON.is_error/subtype            └─ stdout (kubectl logs)
claude-creds(mount)┘   4. git push branch + run-report.json
```

## Beslissingen

### Succes uit de JSON, niet uit de exit-code (clevere valkuil)
`claude -p` kan óók een non-zero exit-code geven bij kostenrem-bereikt, stdin-overflow
en auth-fout — dus `$?` is een onbetrouwbare succesindicator. Het verdict komt uit
het JSON-eindobject: `is_error` (bool) en `subtype`. De exit-code loggen we mee, maar
sturen erop niet. Parser is defensief: geen parseerbare JSON → verdict = error;
ontbrekende velden = afwezig, nooit hard indexeren.

### Git-auth: single-repo fine-grained PAT over HTTPS
Er is geen egress-proxy (de CNI filtert native op FQDN), dus de deploy-key-vs-proxy
botsing bestaat niet meer. Keuze (Mark, 2026-07-05): PAT houden. Een fine-grained PAT
scoped tot één repo + `contents:write`, geleverd via een per-node secret, per node
intrekbaar. De PAT gaat via een git credential-helper die uit env leest — nooit in de
URL, reflog of logs.

### Kostenrem: `--max-budget-usd` (preventief) + `total_cost_usd` (audit)
`claude` 2.1.201 heeft `--max-budget-usd`: een harde dollar-cap ín de run. Dat is de
preventieve kostenrem per change (env `HABITAT_MAX_BUDGET_USD`, default $5). De
gerealiseerde `total_cost_usd` gaat in het run-rapport voor audit/escalatie.
`add-dispatch` legt daar `activeDeadlineSeconds` als wall-clock-backstop overheen.

### Auth: sub-first (subscription-credentials)
Per de sub-first-lijn draait de worker op Claude-subscription-auth, niet op een
API-key. Het `claude-credentials`-secret (de OAuth-credentials) wordt read-only op
`/var/run/claude` gemount; de entrypoint kopieert het naar
`~/.claude/.credentials.json` (0600). `ANTHROPIC_API_KEY` blijft een fallback.
Token-refresh loopt over `*.anthropic.com` (in de egress-allowlist).

### Deps: alleen worker-eigen tools gebakken
Het image bakt `claude`/`uv`/`git` op gepinde versies. Doel-repo-deps (de repo kan
z'n eigen `uv sync`/`npm ci` willen) worden runtime geïnstalleerd. Daarom bevat de
egress-allowlist pypi+npm. De clevere valkuil zou zijn "alles te bakken" — dat kan
niet, want de worker weet vooraf niet welke doelrepo of toolchain er komt.

### Permission-mode: `bypassPermissions`
Headless draait de agent vast als hij op tool-approval wacht die nooit komt. Daarom
`--permission-mode bypassPermissions`. Verantwoord omdat de échte grens de kooi is
(egress-policy + RBAC + wegwerp-Job), niet de tool-approval binnen de container.

### `run-report.json` in de branch
`kubectl logs` is vluchtig (Job wordt opgeruimd via `ttlSecondsAfterFinished`).
Daarom schrijft de worker een `run-report.json` (rol, change, run-id, verdict,
`total_cost_usd`, num_turns, timestamps) mee de branch in: duurzame audit die
`add-audit-report` consumeert, los van de logstream.

## Wat deze change NIET doet
- Geen Job-manifest / `activeDeadlineSeconds` — dat is `add-dispatch`.
- Geen NetworkPolicy / secrets — dat is `add-cage`.
- Geen rol-definities — die zijn `.claude/agents/`-files in de doelrepo.

## Rook-test (DoD)
`docker run` met de vier env-vars + een test-PAT tegen een testrepo: image clonet,
draait `claude -p`, pusht een branch met `run-report.json`. Lokaal, buiten het
cluster, vóór de kooi bestaat.
