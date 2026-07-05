## 1. Job-template

- [x] 1.1 `dispatch/job-template.yaml`: geparametriseerd (envsubst-vars)
- [x] 1.2 `restartPolicy: Never`, `backoffLimit: 0`, `activeDeadlineSeconds`, `ttlSecondsAfterFinished`, `terminationGracePeriodSeconds`
- [x] 1.3 Label `habitat/component: worker` (egress-policy) + SA `role-<rol>` + `automountServiceAccountToken: false`
- [x] 1.4 Auth sub-first: `claude-credentials` read-only gemount; `GIT_PAT` via `secretKeyRef`; resources/securityContext

## 2. dispatch-script

- [x] 2.1 `dispatch/dispatch.sh <rol> <change> <repo> [run-id]`: rendert (envsubst) + `kubectl apply`
- [x] 2.2 Wacht op pod, streamt logs, archiveert log naar bestand
- [x] 2.3 Uitkomst uit `Job.status.conditions` (`Complete` vs `Failed`/`DeadlineExceeded`), niet uit exit-code
- [x] 2.4 `KUBECTL`-override zodat de orchestrator zijn eigen kubeconfig/SA kan gebruiken

## 3. Verificatie (DoD)

- [x] 3.0 Job-manifest server-side gevalideerd (`apply --dry-run=server`) tegen de cluster-API — geaccepteerd
- [ ] 3.1 Image op GHCR (publiek, SHA-getagd) — GEBLOKKEERD: `gh`-token mist `write:packages` (Mark)
- [x] 3.2 Test-secret `pat-node-01` in `agents` (dummy); `claude-credentials` uit subscription (prod: SOPS)
- [ ] 3.3 Cluster-run: `dispatch.sh builder smoke MWest2020/habitat-testrepo` → Job draait, egress via worker-label, logs streamen, branch + `run-report.json` gepusht
- [ ] 3.4 Status correct afgelezen (`Complete`/`Failed`)
- [ ] 3.5 Groen: verdict=ok met een echte `claude -p` via subscription-credentials in de Job
