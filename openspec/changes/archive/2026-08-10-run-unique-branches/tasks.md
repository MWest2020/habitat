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
- [x] 3.3 Nieuwe image (4b11c83); cluster-verificatie met `chain.sh` op
      habitat-testrepo (2026-08-10): run-unieke branchnamen bevestigd
      (`habitat/<rol>/<change>-<datum>-<tijd>-<rand>`), `dispatch.sh` print de
      branch, en de reviewer checkte aantoonbaar de builder-branch uit
      (`HABITAT_BASE_BRANCH`-threading werkt). De keten-gate stopte bij de
      reviewer-FAIL (security draaide niet) → verdict-propagatie werkt.
      _NB: de reviewer-FAIL was een fixture-artefact (add-greeting-taak 2.1 is
      per constructie onbewijsbaar: de verify-gate laat geen exitcode-artefact
      achter), niet een gebrek in deze change. Fixture-polish + de door de
      reviewer genoemde audit-telling (rapport 2 vs. commit 6 bestanden) als
      losse follow-up genoteerd._
