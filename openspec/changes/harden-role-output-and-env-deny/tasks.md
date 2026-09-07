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

- [ ] 5.1 Merge naar `main` → workflow `worker-image.yml` bouwt een nieuw
      image op de merge-SHA
- [ ] 5.2 Dispatchen met dat image; controleren dat een builder
      `deploy/.env.example` nu wél kan bewerken en dat een rol geen
      1-woord-`summary` meer kan afleveren
