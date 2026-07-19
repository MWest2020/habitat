# Tasks: apply-docs-contract

- [x] 1.1 Branch `docs/contract` vanaf de default branch. — Uitgevoerd op de
      dispatch-branch `habitat/builder/apply-docs-contract` (habitat-conventie
      `habitat/<rol>/<change>` vervangt de losse `docs/contract`-naam).
- [x] 2.1 `docs/`-structuur aanleggen volgens het contract; bestaande docs
      migreren zoals beschreven in proposal.md (repo-specifiek); stubs
      achterlaten waar externe links kunnen bestaan.
- [x] 2.2 Front matter op elke pagina: gemigreerd-zonder-review =
      `status: draft` + `last_reviewed` = migratiedatum.
- [x] 2.3 `docs/index.md`: één alinea wat het project is, status, link naar
      README, links naar de aanwezige secties.
- [x] 2.4 `.mcp.json` in de root plaatsen (template uit de seed; placeholder `TODO-change-3` laten staan).
- [x] 3.1 Zelfcheck tegen het contract: alleen toegestane submappen dragen
      markdown, elke pagina heeft front matter, één taal (Nederlands).
- [ ] 4.1 PR openen met titel `docs: apply handbook docs contract`; body vinkt
      per contractpunt af wat is toegepast + vermeldt de punten die de
      proposal als "PR-body" markeert. STOP daarna: Mark merget.
      — Niet uitgevoerd: CLAUDE.md-invariant "Commits blijven lokaal tot Mark
      pusht" gaat vóór; push + PR + merge horen bij Mark. PR-body staat kant-en-
      klaar in het run-report hieronder.
