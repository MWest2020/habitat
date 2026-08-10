# run-unique-branches

## Why

De worker pusht nu naar `habitat/<rol>/<change>` en valt bij een bestaande
branch (eerdere run) terug op `…-<run_id>` (`entrypoint.sh`, "nooit
force-pushen"). Gevolg: de branchnaam is **niet deterministisch** — een
eerste run krijgt de kale naam, een re-run de suffix. Erger: bij een
**builder-retry** landt de nieuwe run op de suffix-branch, terwijl de
reviewer/security-stap `HABITAT_BASE_BRANCH=habitat/builder/<change>` (de kale
naam) gebruikt → die leest dan de oude builder-run.

Besluit Mark 2026-08-10: houd de niet-destructieve waarde (nooit force-pushen,
elke run bewaard) en maak in plaats daarvan de branch **altijd** run-uniek, met
de keten die de builder-branch expliciet doorgeeft.

## What Changes

- **`worker/entrypoint.sh`**: `BRANCH=habitat/<rol>/<change>-<run_id>` en push
  daar altijd naartoe. De kale-push-met-fallback vervalt (geen collision meer
  mogelijk → geen force nodig, elke run blijft bewaard).
- **`dispatch/dispatch.sh`**: schone `RUN_ID`-default (`<datum>-<tijd>-<rand>`
  i.p.v. `<rol>-<change>-<tijd>`, want rol/change staan al in het pad); print de
  landende branch machine-leesbaar (`[dispatch] branch=<naam>`); de AFGEROND-
  regel noemt de echte branch.
- **`dispatch/chain.sh`** (nieuw): draait architect → builder → reviewer →
  security en **threadt de builder-branch** als `HABITAT_BASE_BRANCH` naar
  reviewer en security.
- Docs (`docs/reference/dispatch.md`) en spec (`worker-execution`) bijgewerkt.

## Impact

- Wijziging onder `worker/**` → nieuwe worker-image (CI tagt per SHA); daarna de
  `WORKER_IMAGE`-pin bij dispatch bijwerken.
- Deterministische, niet-destructieve branchnamen; de rol-keten werkt ook na een
  retry. Geen force-push, elke run bewaard (conform de bestaande waarde).
