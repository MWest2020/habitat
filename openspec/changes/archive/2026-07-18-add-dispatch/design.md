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

### Secrets via de pod-spec, niet via de SA
De rol-SA heeft geen API-token en geen secret-leesrecht; de kubelet mount de
secrets op basis van de pod-spec. Zo kan een worker de gemounte Claude-credentials
(sub-first) en zijn node-`GIT_PAT` gebruiken zonder de kube-API te kunnen bevragen.

### Token-refresh: één schrijver, sync-at-dispatch (clevere valkuil)
De subscription-token in `claude-credentials` verloopt na ~8u. De clevere valkuil
is de worker zelf laten refreshen (de creds staan schrijfbaar in `~/.claude/`):
een refresh in een wegwerp-Job kan de refresh-token roteren zonder dat die
terugkomt in het cluster-secret, en parallelle Jobs geven refresh-races. Saai
alternatief: de orchestrator is de énige schrijver en synct het secret bij elke
dispatch vanaf `~/.claude/.credentials.json` op de orchestrator-host — diens
eigen Claude-sessie houdt dat bestand vers. `dispatch.sh` waarschuwt als de token
vóór de Job-deadline verloopt, en slaat de sync over met `CLAUDE_CREDS_FILE=`
(leeg) of als het bronbestand ontbreekt (secret blijft dan zoals uitgerold).

## Parameters (env voor dispatch.sh / envsubst)
`HABITAT_ROLE`, `HABITAT_CHANGE`, `HABITAT_REPO`, `HABITAT_RUN_ID`,
`HABITAT_MAX_BUDGET_USD` (default 5.00), `ACTIVE_DEADLINE_SECONDS` (default 1800),
`PAT_SECRET` (default `pat-node-01`), `WORKER_IMAGE` (verplicht, SHA-getagd),
`CLAUDE_CREDS_FILE` (default `~/.claude/.credentials.json`; leeg = geen sync).

## Wat deze change NIET doet
- Geen orchestrator-mandaat/tmux — dat is `add-orchestrator`.
- Geen HTML-run-rapport — dat is `add-audit-report`.
- Geen merge-automatisering (v0: merges bij Mark).
