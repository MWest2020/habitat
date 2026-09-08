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
- [ ] 3.2 `shellcheck` op de shellscripts van deze repo draaien en de uitvoer in
      de run-output zetten — dat is meteen het bewijs dat het commando werkt.
      (Deze run draait nog op de vorige image; als shellcheck er niet is, meld dat
      dan expliciet in plaats van de taak af te vinken.)
- [ ] 3.3 CI groen (verify + docs-gates).

## 4. Uitrol

- [ ] 4.1 Na merge: image-build geslaagd, nieuwe tag genoteerd.
- [ ] 4.2 Eén dispatch op de nieuwe tag waarin een rol shellcheck daadwerkelijk
      draait.
