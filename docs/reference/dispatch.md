---
status: draft
last_reviewed: 2026-07-29
---

# Dispatch-contract

Feiten over `dispatch/dispatch.sh` en het gerenderde Job-manifest
(`dispatch/job-template.yaml`). Eén rol-run = één K8s-Job in namespace `agents`.
De uitkomst komt uit `Job.status.conditions`, niet uit de pod-exit-code.

## Aanroep

```
dispatch.sh <rol> <change> <repo> [run-id]
```

| Argument | Verplicht | Betekenis |
|---|---|---|
| `<rol>` | ja | `architect` \| `builder` \| `reviewer` \| `security` |
| `<change>` | ja | change-naam (map onder `openspec/changes/`) |
| `<repo>` | ja | doelrepo (`owner/repo` of URL) |
| `[run-id]` | nee | default `<rol>-<change-geslugd>-<YYYYmmdd-HHMMSS>` |

De worker dwingt per rol een settings-allowlist (`worker/settings/<rol>.json`,
deny-by-default via `--permission-mode dontAsk`) en een output-JSON-schema
(`worker/schemas/<rol>.json`) af; zie [`roles.md`](roles.md).

## Environment-variabelen

| Variabele | Default | Rol |
|---|---|---|
| `WORKER_IMAGE` | — (verplicht) | image per commit-SHA, bv. `ghcr.io/mwest2020/habitat-worker:<sha>`; nooit `latest` |
| `KUBECTL` | `kubectl` | kubectl-binary/-wrapper; mag een remote wrapper zijn (`KUBECTL="ssh <host> kubectl"`) — zie [Remote kubectl](#remote-kubectl) |
| `HABITAT_BASE_BRANCH` | leeg | basisbranch voor de run |
| `HABITAT_MAX_BUDGET_USD` | `5.00` | kostendrempel per change |
| `ACTIVE_DEADLINE_SECONDS` | `1800` | `activeDeadlineSeconds` op de Job |
| `PAT_SECRET` | `pat-node-01` | secret met `GIT_PAT` (git-auth over HTTPS) |
| `HABITAT_LOGDIR` | `./run-logs` | doelmap voor gearchiveerde logs |
| `CLAUDE_CREDS_FILE` | `~/.claude/.credentials.json` | bron voor de `claude-credentials`-sync per dispatch (subscription-token verloopt ~8u); leeg = sync overslaan. Overbodig zodra het Secret `claude-oauth-token` bestaat — zie hieronder |

## Worker-auth

De entrypoint kiest, in deze volgorde:

1. **`CLAUDE_CODE_OAUTH_TOKEN`** uit het optionele Secret `claude-oauth-token`
   (sleutel `token`). Een `claude setup-token`-token: subscription-auth die een
   jaar geldig is, dus geen sync per dispatch en geen verlopen token halverwege
   een keten. Aanmaken op een host met browser-toegang:

   ```
   claude setup-token
   kubectl -n agents create secret generic claude-oauth-token --from-literal=token=<token>
   ```

   Daarna mag `CLAUDE_CREDS_FILE=` (leeg) en kan het Secret
   `claude-credentials` weg; beide mounts zijn `optional`.
2. **Gemounte sessie-credentials** (`claude-credentials`) — het oude
   sub-first-pad, alleen vers zolang `dispatch.sh` ze meesynchroniseert.
3. **`ANTHROPIC_API_KEY`** — Console-key, verloopt niet, maar rekent per token
   af buiten het abonnement om.

Workers refreshen nooit zelf: een refresh in een wegwerp-Job kan de
refresh-token roteren zonder te persisteren, wat bij parallelle runs racet.
Vandaar dat optie 1 de voorkeur heeft boven een steeds opnieuw te synchroniseren
sessie-token.

Het script exporteert daarnaast `JOB_NAME`, `HABITAT_ROLE`, `HABITAT_CHANGE`,
`HABITAT_REPO` en `HABITAT_RUN_ID` naar het manifest (via `envsubst`).

## Job-conventies

- **Naam**: `habitat-<rol>-<change-geslugd>-<epoch>`.
- **Labels**: `app.kubernetes.io/part-of: habitat`, `habitat/component: worker`
  (selecteert de worker-egress-`CiliumNetworkPolicy`), `habitat/role: <rol>`,
  `habitat/run-id: <run-id>`.
- **Isolatie**: `serviceAccountName: role-<rol>`, `automountServiceAccountToken: false`,
  `backoffLimit: 0`, `restartPolicy: Never`, `ttlSecondsAfterFinished: 3600`,
  capabilities `drop: ["ALL"]`, `allowPrivilegeEscalation: false`.

## Branch- en run-report-conventie

- De worker pusht een **run-unieke** branch
  `habitat/<rol>/<change>-<run_id>` in de doelrepo (nooit force, nooit
  destructief — een retry overschrijft de vorige run niet). `dispatch.sh` print
  de landende branch als `[dispatch] branch=<naam>`.
- Naast de code staat `run-report.json` op die branch. De `diff_hash` daarin
  dekt uitsluitend de agent-codewijziging; **exact de door habitat gegenereerde
  artefacten van de run** vallen erbuiten — op vaste naam plus de run-id, zónder
  wildcards (`.habitat/audit.jsonl`, `.habitat/run-report-<run-id>.html`,
  `.habitat/run-output-<run-id>.md`, `run-report.json`). Niet de hele
  `.habitat/`-map en geen naam-wildcard, zodat élk ander bestand dat de agent
  onder `.habitat/` schrijft wél meetelt (geen smokkelkanaal). Het exacte
  reproductie-commando (mét de concrete run-id) staat in het veld
  `diff_hash_scope` van `run-report.json`.
- De agent-eind-uitvoer (`result`) staat als `.habitat/run-output-<run-id>.md`
  op de branch. Habitat schrijft dit bestand **altijd** — ook zonder leesbaar
  `result` (dan een placeholder) — ná de diff-hash, zodat het artefact
  deterministisch habitat-eigendom is en een agent er geen eigen versie voor kan
  smokkelen. Een onleesbare `.habitat/audit.jsonl`-regel is fail-closed: het
  rapport crasht niet en toont zo'n regel als expliciet gebroken rij.
- Reviewer/security bouwen op de **builder-branch** via
  `HABITAT_BASE_BRANCH`. Gebruik `chain.sh` (zie hieronder) zodat die branch
  automatisch wordt doorgegeven; handmatig kan ook met de naam uit de
  builder-dispatch-output.
- Merges naar `main` doet **altijd Mark**; dispatch merget nooit.

## Volle keten: `chain.sh`

`dispatch/chain.sh <change> <repo>` draait architect → builder → reviewer →
security en geeft de run-unieke builder-branch automatisch door aan reviewer en
security (`HABITAT_BASE_BRANCH`). Zelfde env als `dispatch.sh` (`WORKER_IMAGE`
verplicht).

## Uitkomst

`dispatch.sh` wacht op een **terminale** `Job.status.conditions` (`Complete`
of `Failed`) en vertaalt die naar een exit-code. De wachttimeout is
`ACTIVE_DEADLINE_SECONDS + 600s` — ruim genoeg voor scheduling en een cold
image-pull, zodat een trage start niet als "onbekend" eindigt.

| Conditie | Melding | Exit |
|---|---|---|
| `Complete` | `AFGEROND — lees run-report.json op branch habitat/<rol>/<change>-<run_id>` | `0` |
| `Failed` (`DeadlineExceeded`) | `TIME-OUT — branch mogelijk deels/niet gepusht` | `1` |
| `Failed` (overig) | `MISLUKT (<reason>)` | `1` |
| geen conditie binnen de timeout | `GEEN uitkomst binnen <n>s` | `2` |

De logs worden gestreamd (`kubectl logs -f` zodra de pod draait) en
gearchiveerd naar `$HABITAT_LOGDIR/<job-naam>.log`.

### Remote kubectl

Draai je vanaf een host zonder cluster-toegang, dan is `KUBECTL` een wrapper:

```
KUBECTL="ssh -o BatchMode=yes <host> kubectl"
```

Let op: zo'n wrapper geeft het commando als één string door, waarna de shell op
de *doelhost* het opnieuw parseert. Argumenten met spaties, haakjes of
aanhalingstekens overleven dat niet. Daarom leest `dispatch.sh` de
Job-condities via `-o json` + een lokale `python3`-filter (`job_conditions()`)
in plaats van een jsonpath met `[?(@.status=="True")]`: die template gaf op de
doelhost `syntax error near unexpected token '('`, `2>/dev/null` slikte de fout
op, en **elke** run — ook een geslaagde — eindigde als `GEEN uitkomst` met exit
2 (waargenomen 2026-09-05 op een reviewer-run die PASS was).

Bouw je hier iets bij, houd kubectl-argumenten dan vrij van spaties en
aanhalingstekens, of haal `-o json` op en filter lokaal.

## Runbook: cluster-livetests (add-role-architecture 3.1–3.3)

Draai dit op een host met `kubectl`-toegang tot het `agents`-cluster en een
verse Claude-sessie (voor de credentials-sync). Plak blok voor blok.

### 0. Pre-flight — image-tag en variabelen

De worker-image is per commit-SHA getagd (`worker-image.yml` → `github.sha`).
Pak de SHA van de laatste geslaagde build i.p.v. te gokken:

```bash
# vanuit een clone van MWest2020/habitat, op main
WORKER_SHA=$(gh run list --workflow worker-image.yml --branch main \
  --status success --limit 1 --json headSha -q '.[0].headSha')
export WORKER_IMAGE="ghcr.io/mwest2020/habitat-worker:${WORKER_SHA}"
export CHANGE="livetest-$(date +%Y%m%d)"   # naam van de test-change op de testrepo
export REPO="MWest2020/habitat-testrepo"
echo "image=$WORKER_IMAGE change=$CHANGE repo=$REPO"
# sanity: de worker-code-inhoud onder test zit in commit 2f2be16 (laatste worker/**).
kubectl -n agents get sa,role,rolebinding | grep -i architect   # role-architect RBAC aanwezig?
```

### 3.1 + 3.3 — volle keten via `chain.sh`

```bash
dispatch/chain.sh "$CHANGE" "$REPO"
```
Draait architect → builder → reviewer → security en threadt de run-unieke
builder-branch automatisch naar reviewer en security. Verwacht: architect →
`AFGEROND`, schone boom (`diff_hash` = leeg-hash); builder → `AFGEROND`,
`GREETING.md`, Stop-hook-verify geslaagd; reviewer/security → `AFGEROND` met
`diff_hash` = leeg-hash (nul writes → read-only afgedwongen). Verdict-propagatie:
een rol-`FAIL` zet `VERDICT=failed` → Job `Failed`.

Losse rollen kan ook met `dispatch.sh <rol> <change> <repo>`; pak dan de
builder-branch uit `[dispatch] branch=…` en geef die als `HABITAT_BASE_BRANCH`
aan reviewer/security.

Extra check — **Stop-hook blokkeert een builder met falende verify**: draai de
builder met `HABITAT_BASE_BRANCH=test/failing-verify` (een branch waarvan
`scripts/verify.sh` faalt) en verwacht Job `Failed`.

### 3.2 — idempotentie-smoke

```bash
dispatch/dispatch.sh builder "$CHANGE" "$REPO"   # run-a
dispatch/dispatch.sh builder "$CHANGE" "$REPO"   # run-b (andere run-unieke branch)
# vergelijk het diff_hash-veld in run-report.json op beide branches → gelijk
```

Na groene 3.1–3.3: vink ze af in
`openspec/changes/add-role-architecture/tasks.md`, draai
`openspec validate add-role-architecture` en archiveer.

## Optionele taak-referentie (amend-worker-task-ref)

`HABITAT_TASK_REF` (optioneel) = een pad relatief aan de doelrepo-root naar een
taak/context-bestand. De worker leest het ná de checkout uit de gecloonde repo en
voegt de inhoud als context aan de rol-prompt toe — dit is git, geen nieuw
invoerkanaal. Pad-begrenzing binnen de repo; een absoluut pad, `..`, of een
niet-bestaand bestand is fail-closed (exit, geen run). Gebruikt door de
boomhuis-brug (add-habitat-bridge): de orchestrator commit het taakbestand in de
doelrepo en geeft het pad mee.
