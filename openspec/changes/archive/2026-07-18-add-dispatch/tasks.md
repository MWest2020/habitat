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
- [x] 3.1 Image op GHCR (SHA-getagd), door de nodes gepulld via `ghcr-pull` pull-secret
- [x] 3.2 Secrets in `agents`: `claude-credentials` (subscription) + `pat-node-01` (gh-token); prod: SOPS
- [x] 3.3 Cluster-run: `dispatch.sh builder smoke MWest2020/habitat-testrepo` → Job op node, egress via worker-label, branch + `run-report.json` gepusht
- [x] 3.4 Status correct afgelezen (`Complete=CompletionsReached`)
- [x] 3.5 GROEN: verdict=ok, echte `claude -p` (7 turns, $0.19) via subscription-credentials; HELLO.md +1 regel

## 4. Randvoorwaarden (ontdekt tijdens live run)

- [x] 4.1 Node-VM's vereisen AVX2 (Bun-runtime) → Proxmox CPU-type `host` (Mark, gedaan)
- [x] 4.2 Subscription-token verloopt (~8u) → refresh-strategie: sync-at-dispatch door de
      orchestrator (énige schrijver) vanaf `~/.claude/.credentials.json`; waarschuwing als de
      token vóór de Job-deadline verloopt; `CLAUDE_CREDS_FILE=` slaat de sync over. Workers
      refreshen nooit zelf (rotatie-race). Zie design.md; blok functioneel getest met
      gestubde kubectl (verlopen/vers/geen creds) op 2026-07-18.
