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
| `KUBECTL` | `kubectl` | kubectl-binary/-wrapper |
| `HABITAT_BASE_BRANCH` | leeg | basisbranch voor de run |
| `HABITAT_MAX_BUDGET_USD` | `5.00` | kostendrempel per change |
| `ACTIVE_DEADLINE_SECONDS` | `1800` | `activeDeadlineSeconds` op de Job |
| `PAT_SECRET` | `pat-node-01` | secret met `GIT_PAT` (git-auth over HTTPS) |
| `HABITAT_LOGDIR` | `./run-logs` | doelmap voor gearchiveerde logs |
| `CLAUDE_CREDS_FILE` | `~/.claude/.credentials.json` | bron voor de `claude-credentials`-sync per dispatch (subscription-token verloopt ~8u); leeg = sync overslaan |

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

- De worker pusht een branch `habitat/<rol>/<change>` in de doelrepo.
- Naast de code staat `run-report.json` op die branch.
- Merges naar `main` doet **altijd Mark**; dispatch merget nooit.

## Uitkomst

`dispatch.sh` leest `Job.status.conditions` en vertaalt die naar een exit-code:

| Conditie | Melding | Exit |
|---|---|---|
| `Complete` | `AFGEROND — lees run-report.json op branch habitat/<rol>/<change>` | `0` |
| `Failed` (`DeadlineExceeded`) | `TIME-OUT — branch mogelijk deels/niet gepusht` | `1` |
| `Failed` (overig) | `MISLUKT (<reason>)` | `1` |
| onbekend | `onbekende status` | `2` |

De logs worden gestreamd (`kubectl logs -f`) en gearchiveerd naar
`$HABITAT_LOGDIR/<job-naam>.log`.

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

### 3.1 — per rol op de testrepo

```bash
# architect: schone boom + schema-valide plan in de output, verdict PASS
dispatch/dispatch.sh architect "$CHANGE" "$REPO"

# builder: bouwt de change en pusht branch habitat/builder/$CHANGE
dispatch/dispatch.sh builder "$CHANGE" "$REPO"

# reviewer: leest de builder-branch, mag NIET schrijven (Write/Edit geweigerd in de pod-log)
HABITAT_BASE_BRANCH="habitat/builder/$CHANGE" \
  dispatch/dispatch.sh reviewer "$CHANGE" "$REPO"

# security: idem — Write/Edit geweigerd in de pod-log
HABITAT_BASE_BRANCH="habitat/builder/$CHANGE" \
  dispatch/dispatch.sh security "$CHANGE" "$REPO"
```

Verwacht: architect → `AFGEROND`, plan in output, schone boom; reviewer/security
→ in `run-logs/<job>.log` staat een geweigerde `Write`/`Edit` (deny-by-default);
builder → `AFGEROND` met branch `habitat/builder/$CHANGE`.

Extra check — **Stop-hook blokkeert een builder met falende verify**: draai de
builder op een change waarvan `scripts/verify.sh` faalt en verwacht
`MISLUKT`/Job `Failed` (de Stop-hook laat de run niet groen afsluiten).

### 3.2 — idempotentie-smoke

```bash
dispatch/dispatch.sh architect "$CHANGE" "$REPO" "run-a"
dispatch/dispatch.sh architect "$CHANGE" "$REPO" "run-b"
# vergelijk het diff_hash-veld in run-report.json op beide branches → gelijk
```

### 3.3 — end-to-end keten

Draai architect → builder → reviewer → security op één échte spoke-change en
controleer dat de verdicts de keten sturen (een rol-`FAIL` zet `VERDICT=failed`
→ Job `Failed` → dispatch stopt de keten; zie tabel onder *Uitkomst*).

Na groene 3.1–3.3: vink ze af in
`openspec/changes/add-role-architecture/tasks.md`, draai
`openspec validate add-role-architecture` en archiveer.
