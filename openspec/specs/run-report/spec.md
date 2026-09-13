# run-report Specification

## Purpose

Het run-rapport: één HTML-bestand dat zichzelf uitlegt, zonder server.

Een audit die je alleen kunt lezen met het systeem dat hem maakte, is een audit
die je in de praktijk niet leest. Daarom een single-file rapport dat je kunt
mailen, bewaren en over een jaar nog openen.

Het verifieert de hashketen **in de browser**. Dat is de reden dat dit een eigen
capability is en geen opmaaklaagje: een rapport dat zegt dat de keten klopt
zonder dat de lezer dat zelf kan narekenen, vraagt precies het vertrouwen dat de
keten moest vervangen.
## Requirements
### Requirement: Zelfstandig single-file HTML-run-rapport

Elke run SHALL een `run-report-<run_id>.html` genereren: één bestand,
systeemfonts, geen CDN of externe requests, met diff-samenvatting, verdict,
kosten/turns en de audit-hashketen. Het rapport SHALL **buiten de werkboom van de
doelrepo** geschreven worden en dus **niet** meegecommit of gepusht worden; de
doelrepo houdt uitsluitend de wijziging van de agent. De run-artefacten SHALL de
operator bereiken via het Job-log en daar **lokaal** bewaard worden, met een
retentie van **veertien dagen**.

#### Scenario: Rapport is zelfstandig

- **WHEN** het HTML-rapport in een browser wordt geopend zonder netwerk
- **THEN** rendert het volledig (geen externe scripts, fonts of afbeeldingen)

#### Scenario: De doelrepo blijft schoon

- **WHEN** een run een branch pusht
- **THEN** bevat die branch alleen de wijziging van de agent — geen
  `run-report-<id>.html`, geen `run-output-<id>.md`, geen `run-report.json` en
  geen `.habitat/audit.jsonl`

#### Scenario: De operator houdt de artefacten

- **WHEN** de run klaar is
- **THEN** staan de artefacten byte-identiek in de lokale bewaarplek van de
  operator, herleidbaar per repo en run-id
- **AND** worden artefacten ouder dan veertien dagen verwijderd

### Requirement: In-browser verificatie van de hashketen

Het HTML-rapport SHALL de audit-keten met vanilla JS (`crypto.subtle`) herberekenen
en per schakel geldig/ongeldig tonen, zodat de lezer zonder tooling kan verifiëren.

#### Scenario: Geldige keten

- **WHEN** de keten intact is
- **THEN** toont het rapport elke schakel als geldig (✓)

#### Scenario: Gebroken keten

- **WHEN** een regel is gemanipuleerd
- **THEN** toont het rapport de betreffende schakel als ongeldig (✗)

