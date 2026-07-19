---
status: draft
last_reviewed: 2026-07-12
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
| `<rol>` | ja | `builder` \| `reviewer` \| `security` |
| `<change>` | ja | change-naam (map onder `openspec/changes/`) |
| `<repo>` | ja | doelrepo (`owner/repo` of URL) |
| `[run-id]` | nee | default `<rol>-<change-geslugd>-<YYYYmmdd-HHMMSS>` |

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
