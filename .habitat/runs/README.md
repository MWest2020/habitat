# Bewaarde run-artefacten

Per-run transcripts en HTML-rapporten van dispatchte Jobs, hier geborgd
voordat de tijdelijke `habitat/{builder,reviewer,security}/*`-branches in de
doelrepo's zijn opgeruimd (2026-09-04). Die branches bevatten geen code die
niet in `main` zit — alle bijbehorende OpenSpec-changes zijn gemerged en
gearchiveerd — maar wél de enige kopie van deze audit-artefacten.

- `wordsworth/` — 30 runs (builder/reviewer/security) over 11 changes,
  9-19 juli 2026, uit MWest2020/wordsworth.
- `habitat/` — 2 runs over `apply-docs-contract`, 12 juli 2026, uit deze repo.
- `internetnl-cli/` — 11 runs over `polish-supporter-mail` en `facade-followups`,
  4-5 september 2026, uit MWest2020/internetnl-cli. Beide changes zijn daarna
  buiten de kooi afgemaakt en gemerged (PR #1 en #2).

`audit.jsonl` per map is de ontdubbelde samenvoeging van de audit-regels van
die branches. De geaggregeerde weergave staat in `docs/audit-dashboard.html`.
