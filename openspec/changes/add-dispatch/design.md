# Design — dispatch

## Stroom

```
dispatch.sh <rol> <change> <repo> [run-id]
   │  envsubst job-template.yaml  →  kubectl apply -f -
   ▼
K8s Job (namespace agents, label habitat/component=worker, SA role-<rol>)
   │  worker draait (clone → claude -p → push branch + run-report.json)
   ▼
dispatch.sh:  kubectl logs -f   →   leest Job.status.conditions
   │
   ├─ Complete            → run afgerond (lees run-report.json op de branch)
   ├─ Failed/DeadlineExceeded → time-out (branch mogelijk deels/niet gepusht)
   └─ Failed/<anders>     → mislukt (pod-exit != 0)
```

## Beslissingen

### Bare template + envsubst, geen Helm/Kustomize voor de Job
De Job wordt per run imperatief gerenderd en toegepast; hij hoort niet in de
cage-kustomization (dat is de staande infra). `envsubst` op een diffbaar
`job-template.yaml` is de saaiste render die werkt — geen templating-engine.

### Uitkomst uit Job.status.conditions, niet uit exit-code (clevere valkuil)
Een ge-SIGKILL'de pod (time-out) geeft exit 137 — ononderscheidbaar van andere
oorzaken. De autoritatieve bron is `Job.status.conditions`: `Complete` vs
`Failed` met `reason: DeadlineExceeded`. De orchestrator escaleert op basis
hiervan (time-out ⇒ mogelijk geen/deel-branch; anders ⇒ lees run-report.json).

### `backoffLimit: 0` + `restartPolicy: Never`
Een agent-run is niet idempotent (kan al een deel-branch hebben gepusht). Nooit
stil opnieuw proberen: één shot, één Job, één pod.

### Dubbele kostenrem
`--max-budget-usd` in de worker begrenst de API-kosten preventief;
`activeDeadlineSeconds` op de Job begrenst de wall-clock hard (kill). Samen dekken
ze "duur" én "hangt".

### Secrets via secretKeyRef, niet via de SA
De rol-SA heeft geen API-token en geen secret-leesrecht; de kubelet mount de
secrets op basis van de pod-spec. Zo kan een worker zijn eigen `ANTHROPIC_API_KEY`
en node-`GIT_PAT` gebruiken zonder de kube-API te kunnen bevragen.

## Parameters (env voor dispatch.sh / envsubst)
`HABITAT_ROLE`, `HABITAT_CHANGE`, `HABITAT_REPO`, `HABITAT_RUN_ID`,
`HABITAT_MAX_BUDGET_USD` (default 5.00), `ACTIVE_DEADLINE_SECONDS` (default 1800),
`PAT_SECRET` (default `pat-node-01`), `WORKER_IMAGE` (verplicht, SHA-getagd).

## Wat deze change NIET doet
- Geen orchestrator-mandaat/tmux — dat is `add-orchestrator`.
- Geen HTML-run-rapport — dat is `add-audit-report`.
- Geen merge-automatisering (v0: merges bij Mark).
