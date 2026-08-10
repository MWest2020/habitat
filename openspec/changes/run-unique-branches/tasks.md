# Tasks: run-unique-branches

## 1. Worker + dispatch

- [ ] 1.1 `worker/entrypoint.sh`: `BRANCH=habitat/<rol>/<change>-<run_id>`;
      altijd daarheen pushen; de kale-push-met-`-<run_id>`-fallback vervalt.
      Geen force-push.
- [ ] 1.2 `dispatch/dispatch.sh`: `RUN_ID`-default = `<datum>-<tijd>-<rand>`;
      print `[dispatch] branch=habitat/<rol>/<change>-<run_id>`; AFGEROND-regel
      noemt die branch.
- [ ] 1.3 `dispatch/chain.sh` (nieuw): architect → builder → reviewer →
      security; vangt de builder-branch uit de dispatch-output en geeft die als
      `HABITAT_BASE_BRANCH` mee aan reviewer en security. shellcheck schoon.

## 2. Docs + spec

- [ ] 2.1 `docs/reference/dispatch.md`: branch-conventie (run-uniek) +
      `chain.sh`-gebruik; runbook bijwerken.
- [ ] 2.2 Spec-delta `worker-execution`: Scenario "Push van de resultaat-branch"
      → `habitat/<rol>/<change>-<run_id>`.

## 3. Verify

- [x] 3.1 `shellcheck --severity=warning` schoon op entrypoint.sh, dispatch.sh,
      chain.sh.
- [x] 3.2 Code-review reviewer + security in verse context; bevindingen verwerkt.
      _Beide PASS. Verwerkt: chain.sh stopt nu bij rol-FAIL (dispatch-exit i.p.v.
      `|| true`), reachable "geen branch"-melding, `unset HABITAT_BASE_BRANCH` aan
      het begin. CHANGE-sanitatie: pre-existing en fail-safe (checkout -b weigert
      gevaarlijke vormen) — genoteerd, niet in scope._
- [ ] 3.3 Nieuwe image; cluster-verificatie: `chain.sh` op habitat-testrepo →
      run-unieke branchnamen, reviewer/security lezen aantoonbaar de juiste
      builder-branch; daarna afvinken/archiveren.
