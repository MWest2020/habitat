---
status: draft
last_reviewed: 2026-07-18
---

# Dispatch-contract

Feiten over `dispatch/dispatch.sh` en `dispatch/job-template.yaml`, zoals
geïmplementeerd (change `add-dispatch`).

## Aanroep

```
dispatch.sh <rol> <change> <repo> [run-id]
```

- `rol`: `builder` | `reviewer` | `security` (bepaalt ServiceAccount `role-<rol>`
  en het rolbestand `.claude/agents/<rol>.md` in de **doelrepo**).
- `change`: naam van de OpenSpec-change in de doelrepo.
- `repo`: `owner/repo`, volledige HTTPS-URL of pad.
- `run-id` (optioneel): default `<rol>-<change-slug>-<YYYYMMDD-HHMMSS>`.

## Omgevingsvariabelen

| Variabele | Verplicht | Default | Betekenis |
|---|---|---|---|
| `WORKER_IMAGE` | ja | — | `ghcr.io/mwest2020/habitat-worker:<commit-sha>`, nooit `latest` |
| `KUBECTL` | nee | `kubectl` | Override zodat de orchestrator zijn eigen kubeconfig/SA gebruikt |
| `HABITAT_BASE_BRANCH` | nee | leeg (default branch) | Basisbranch in de doelrepo |
| `HABITAT_MAX_BUDGET_USD` | nee | `5.00` | Doorgegeven aan `claude -p --max-budget-usd` |
| `ACTIVE_DEADLINE_SECONDS` | nee | `1800` | Harde wandkloklimiet van de Job |
| `PAT_SECRET` | nee | `pat-node-01` | Naam van het per-node PAT-secret (`GIT_PAT`-key) |
| `HABITAT_LOGDIR` | nee | `./run-logs` | Map waarin het Job-log wordt gearchiveerd |

## Job-eigenschappen (template)

- Naam `habitat-<rol>-<change-slug>-<epoch>`, namespace `agents`, labels
  `habitat/component=worker` (selecteert de egress-allowlist), `habitat/role`,
  `habitat/run-id`.
- `restartPolicy: Never`, `backoffLimit: 0`, `ttlSecondsAfterFinished: 3600`,
  `terminationGracePeriodSeconds: 10`.
- `serviceAccountName: role-<rol>` met `automountServiceAccountToken: false`.
- Auth sub-first: secret `claude-credentials` read-only gemount op
  `/var/run/claude/credentials.json`; `GIT_PAT` via `secretKeyRef` uit
  `${PAT_SECRET}`.
- Resources: requests 250m/512Mi, limits 2 CPU/2Gi. `imagePullSecrets:
  ghcr-pull` (vervalt zodra het GHCR-package publiek is).

## Uitkomst en conventies

- De uitkomst komt **autoritatief** uit `Job.status.conditions`
  (`Complete` vs `Failed`/`DeadlineExceeded`), niet uit de pod-exit-code.
  Exit-codes van `dispatch.sh`: `0` afgerond, `1` mislukt/time-out, `2` onbekend.
- De worker pusht branch `habitat/<rol>/<change>` in de doelrepo — nooit `main` —
  inclusief `run-report.json` (rol, change, run-id, verdict, `total_cost_usd`,
  turns, exit, timestamp).
- Logs worden gestreamd en gearchiveerd naar `HABITAT_LOGDIR/<job-naam>.log`.
