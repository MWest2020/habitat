# Tasks: robust-dispatch-wait

## 1. Dispatch-wait

- [ ] 1.1 `dispatch/dispatch.sh`: vervang de korte fase-wait + korte
      conditie-poll door één lus die op een terminale Job-conditie wacht met
      timeout `ACTIVE_DEADLINE_SECONDS + 600`; logs best-effort streamen zodra de
      pod draait; "onbekend" alleen bij echte timeout, met duidelijke melding.
      set -e-veilig; shellcheck schoon.

## 2. Docs + spec

- [ ] 2.1 `docs/reference/dispatch.md`: Uitkomst-sectie — wachtgedrag + timeout.
- [ ] 2.2 Spec-delta `job-dispatch`: dispatch bepaalt de uitkomst uit een
      terminale Job-conditie met een timeout die scheduling + image-pull dekt.

## 3. Verify

- [x] 3.1 `shellcheck --severity=warning` schoon.
- [x] 3.2 Code-review in verse context: PASS (set-e-veilig, termineert, cold-pull
      gedekt via Job-niveau activeDeadlineSeconds). Security niet materieel
      (read-only kubectl-polling, geen push/secret/creds).
- [ ] 3.3 Cluster-sanity: een normale dispatch meldt `AFGEROND` (exit 0) zonder
      "onbekend"; daarna afvinken/archiveren.
