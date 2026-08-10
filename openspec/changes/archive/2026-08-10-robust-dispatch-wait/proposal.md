# robust-dispatch-wait

## Why

`dispatch.sh` wachtte ~120s op een lopende pod-fase en daarna ~60s op een
Job-conditie (samen ~180s). Bij een **cold image-pull** of een langere run
haalt de Job die vensters niet, waarna dispatch "onbekende status" (exit 2)
meldt terwijl de Job in werkelijkheid nog draait of prima afrondt. Dat is
waargenomen bij de cluster-livetests (2026-08-10) en maakt de exit-code
onbetrouwbaar — ook voor `chain.sh`, dat op die exit gate't.

## What Changes

- **`dispatch/dispatch.sh`**: één wachtlus die poll't op een **terminale
  Job-conditie** (`Complete`/`Failed`) met timeout `ACTIVE_DEADLINE_SECONDS +
  600s` (ruimte voor scheduling en cold pull). Logs worden best-effort
  gestreamd zodra de pod draait (`logs -f` blokkeert dan tot de pod klaar is —
  natuurlijke wacht én zicht). "onbekend" (exit 2) betekent nu alleen een échte
  timeout (bv. onplanbare pod / image-pull-backoff die de deadline nooit haalt),
  met een duidelijker melding.

## Impact

- Alleen `dispatch/dispatch.sh` (orchestrator-host) — **geen nieuwe
  worker-image nodig**. Betrouwbare exit-codes: `Complete`→0, `Failed`→1,
  echte timeout→2. `chain.sh` gate't nu op een betrouwbaar signaal.
