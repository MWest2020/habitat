# Tasks: add-shellcheck-to-worker

## 1. Image

- [x] 1.1 `shellcheck` toevoegen aan de apt-regel in `worker/Containerfile`,
      in dezelfde regel als `git ca-certificates jq python3` — één laag, één
      `rm -rf /var/lib/apt/lists/*`.
- [x] 1.2 Het commentaar boven die regel noemt shellcheck en waaróm hij erbij
      hoort (allowlist + verify.sh die anders stil een no-op wordt).

## 2. Documentatie

- [x] 2.1 `docs/reference/roles.md`: bij de testrunner-opsomming vastleggen dat
      shellcheck sinds deze change echt in de image zit, zodat "toegestaan" en
      "aanwezig" niet meer uit elkaar kunnen lopen zonder dat het opvalt.

## 3. Gate

- [x] 3.1 `openspec validate add-shellcheck-to-worker --strict` groen.
- [x] 3.2 `shellcheck` op de shellscripts van deze repo draaien en de uitvoer in
      het RUN-ARTEFACT zetten (niet in de repo — zie de noot onderaan) — dat is meteen het bewijs dat het commando werkt.
      (Deze run draait nog op de vorige image; als shellcheck er niet is, meld dat
      dan expliciet in plaats van de taak af te vinken.)
- [x] 3.3 CI groen (verify + docs-gates) — PR #28 en #29. — buiten builder-scope: vereist push,
      en de builder pusht niet (CLAUDE.md: "Commits blijven lokaal tot Mark
      pusht"). Mark bevestigt na push/PR.

## 4. Uitrol

- [x] 4.1 Image-build `success` op `698f8a5`. Tag:
      `ghcr.io/mwest2020/habitat-worker:698f8a5de37eb4b99e4a794bda0b52b657175891` — buiten
      builder-scope, hangt af van merge (builder merget niet).
- [x] 4.2 Dispatch `20260908-201228-7674` op die tag, verdict PASS:
      `shellcheck --version: 0.9.0, aanwezig op /usr/bin/shellcheck`, gedraaid op
      zeven scripts (chain.sh, dispatch.sh, start-tmux.sh, entrypoint.sh en de
      drie hooks) — schoon op twee SC2016-info-meldingen na. — buiten builder-scope, hangt af van 4.1.

> **Noot bij 3.2 — een taakformulering die de verkeerde kant op duwde.**
> De oorspronkelijke tekst zei "de uitvoer in de run-output zetten". De builder
> las dat als een bestand in de repo en committe een
> `.habitat/run-output-…md` van 76 regels. Begrijpelijk, maar het gaat in tegen
> habitat#19 (*"runs en output horen niet in git"*), en `.habitat/runs/` is een
> HISTORISCH archief van vóór die change — geen bestemming voor nieuwe runs.
> Het artefact is niet meegemerged; het staat waar het hoort, in
> `run-logs/artifacts/habitat-/20260908-201228-7674` op de dispatcher. De
> taaktekst is aangepast zodat een volgende run niet dezelfde kant op wordt
> geduwd.
