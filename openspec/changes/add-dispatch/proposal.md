## Why

De worker-image kan draaien en de kooi staat, maar er is nog niets dat een run
*start*. Deze change levert dat: een geparametriseerd Job-manifest en een kaal
dispatch-script dat de orchestrator gebruikt om een rol-run te starten, de logs te
streamen, en de uitkomst (afgerond vs time-out vs mislukt) betrouwbaar af te lezen.
Dit is de laatste schakel voor één volledige builder-loop.

## What Changes

- **Job-template** (`dispatch/job-template.yaml`): een geparametriseerd Job-manifest
  met `restartPolicy: Never`, `backoffLimit: 0` (agent-run niet idempotent),
  `activeDeadlineSeconds` (wall-clock-backstop), `terminationGracePeriodSeconds: 10`,
  `ttlSecondsAfterFinished`, SA per rol, en het label `habitat/component: worker`
  zodat de egress-policy hem selecteert. Secrets via `secretKeyRef`
  (`ANTHROPIC_API_KEY`, `GIT_PAT`).
- **dispatch-script** (`dispatch/dispatch.sh`): rendert het template (envsubst),
  `kubectl apply`, streamt de logs, en leest `Job.status.conditions` om
  `Complete` te onderscheiden van `Failed`+`DeadlineExceeded` — niet uit de
  pod-exit-code. Archiveert de log naar een bestand.

## Capabilities

### New Capabilities

- `job-dispatch`: hoe een rol-run als K8s-Job wordt gestart, begrensd (tijd + kosten),
  gevolgd (logs) en afgelezen (status), zodat de orchestrator autonoom kan
  dispatchen en correct kan escaleren.

### Modified Capabilities

<!-- Geen: er bestaan nog geen specs voor dispatch. -->

## Impact

- Consumeert de env-interface van `add-worker-image` en de namespace/RBAC/secrets van
  `add-cage`. Het worker-label koppelt de Job aan de `worker-egress`-CiliumNetworkPolicy.
- Levert het commando dat het orchestrator-mandaat (`add-orchestrator`) aanroept.
- De kostenrem is dubbel: `--max-budget-usd` in de worker (preventief) én
  `activeDeadlineSeconds` op de Job (wall-clock-backstop).
