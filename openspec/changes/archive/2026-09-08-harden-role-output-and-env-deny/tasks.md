# Tasks: harden-role-output-and-env-deny

## T1. OpenSpec

- [x] 1.1 `proposal.md`, `tasks.md`
- [x] 1.2 Spec-delta `specs/role-architecture/spec.md` (MODIFIED: beide
      requirements)
- Verify: `openspec validate harden-role-output-and-env-deny --strict`

## T2. Schema's

- [x] 2.1 `"minLength": 200` op `summary` in alle vier de rol-schema's
- [x] 2.2 Schema's blijven geldige JSON en geldig JSON Schema
- Verify: `python3 -c "import json;[json.load(open(f)) for f in ...]"`

## T3. Settings

- [x] 3.1 `Read(./.env.*)` en `Read(**/.env.*)` vervangen door de tien
      concrete patronen, in alle vier de rol-settings
- [x] 3.2 `Read(./.env)` en `Read(**/.env)` blijven staan; geen ander
      deny-pad aangeraakt
- Verify: diff toont uitsluitend de `.env`-regels

## T4. Docs

- [x] 4.1 `docs/reference/roles.md`: deny-beschrijving en uitvoereis
- Verify: Nederlands, consistent met de rest van het document

## T5. Uitrol — vraagt Mark

- [x] 5.1 Image gebouwd (`worker-image.yml`, run `success` op `698f8a5`). Tag:
      `ghcr.io/mwest2020/habitat-worker:698f8a5de37eb4b99e4a794bda0b52b657175891`.
      In die image nagemeten met een wegwerp-pod, niet uit de repo afgeleid:
      `/opt/habitat/settings/builder.json` bevat **nul** keer de brede
      `Read(**/.env.*)`, en `/opt/habitat/schemas/builder.json` draagt
      `"minLength": 200`.
- [x] 5.2 Twee builder-runs op die image (`20260908-200654-28727` en
      `20260908-201228-7674`, beide PASS). Wat daarmee is aangetoond, en wat
      niet:

      **Summary-eis: aangetoond.** Beide runs leverden een summary van 233 en
      1409 tekens — ruim boven de 200. De eerste run mét een expliciete
      `deviations`-lijst waarin de rol meldt wat hij níet kon afvinken. Dat is
      precies het gedrag dat de lege `{"summary":"test"}` moest vervangen.

      **`.env.example`: aangetoond op de deny-lijst, niet op een echte edit.**
      De tien concrete patronen in de draaiende image raken `.env.example` niet
      meer; dat is nagemeten in de image zelf. Een edit-pad is hier níet
      uitgevoerd, om een eerlijke reden: habitat heeft zelf geen
      `.env.example`. Dat bewijs valt vanzelf uit de eerstvolgende run op een
      repo die er wel een heeft (internetnl-cli, waar het probleem gevonden is).
      Een dispatch daar puur om dit aan te tonen zou een change-loze run zijn —
      precies wat de eerste 4.4b-poging waardeloos maakte.
