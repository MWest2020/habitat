# Tasks: amend-worker-task-ref

- [x] 1.1 `worker/entrypoint.sh`: na de checkout, als `HABITAT_TASK_REF` gezet is,
      valideer het pad (binnen de repo, geen absoluut/`..`), lees het bestand en
      voeg de inhoud als context aan de prompt toe; fail-closed bij ongeldig/
      ontbrekend pad
- [x] 1.2 `dispatch/job-template.yaml` + `dispatch/dispatch.sh`: `HABITAT_TASK_REF`
      als optionele env doorgeven (leeg = huidig gedrag)
- [ ] 1.3 Test: run met een geldig taakbestand → context zichtbaar in de
      run-prompt; run met een `..`-pad → fail-closed; run zonder de var → gedrag
      ongewijzigd
- [x] 1.4 Kooi-bewijs: `git diff` op `cage/` is leeg; geen wijziging aan
      NetworkPolicies/RBAC/egress
- [x] 1.5 Docs: `docs/reference/dispatch.md` — de optionele taak-referentie +
      de pad-begrenzing

> Consumptie (boomhuis-brug) is een aparte change in boomhuis: de orchestrator
> schrijft het taakbestand in de doelrepo (git) en geeft het pad mee. Mark blijft
> poortwachter.
