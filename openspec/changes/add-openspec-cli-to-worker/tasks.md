## 1. Image

- [x] 1.1 `worker/Containerfile`: `@fission-ai/openspec@1.3.1` op de bestaande
      npm-regel, met een comment over de placeholder-naam en de versiekeuze.

## 2. Allowlist

- [x] 2.1 `Bash(openspec validate *)` in `permissions.allow` van
      `worker/settings/{builder,reviewer,security}.json`.
- [x] 2.2 Geverifieerd dat de regel in `allow` staat en **niet** in `deny`, en dat
      de drie bestanden geldige JSON blijven.
- [x] 2.3 `architect.json` ongemoeid (geen artefact om te valideren).

## 3. Docs + spec

- [x] 3.1 `docs/reference/roles.md`: de CLI en de toegestane aanroep per rol.
- [x] 3.2 Spec-delta op `worker-image-build`: de CLI hoort bij de gepinde tools, en
      een rol kan zijn eigen change valideren.

## 4. Gate

- [x] 4.1 `openspec validate add-openspec-cli-to-worker --strict` groen.
- [x] 4.2 CI groen op de PR (verify + docs-gates) — PR #20, run `success`.
- [x] 4.3 Image-build geslaagd (workflow `worker-image`, run `success` op
      `2155dda`). Tag voor dispatchers:
      `ghcr.io/mwest2020/habitat-worker:2155dda562b452f6a246809dc9aa828ae3f795df`
      In de image geverifieerd met een wegwerp-pod: `openspec --version` → 1.3.1
      op `/usr/local/bin/openspec` — de gepinde versie, niet die van npm.
      (Oude regel, ter referentie:) Na merge: image-build geslaagd en de tag genoteerd, zodat
      dispatchers `WORKER_IMAGE` kunnen verzetten.
- [x] 4.4a Image lokaal gebouwd uit deze Containerfile (`docker build`, exit 0) en
      de inhoud gecontroleerd zonder te draaien (`docker create` + `cp`, want deze
      host kan wel bouwen maar geen containers starten): pakket
      `@fission-ai/openspec 1.3.1` in `/usr/local/lib/node_modules/`, met de
      symlink `/usr/local/bin/openspec` → `bin/openspec.js`.
- [~] 4.4b **Deels.** Eerste dispatch op de nieuwe tag gedraaid (reviewer op
      `add-openspec-cli-to-worker`, MWest2020/habitat): `verdict=ok`,
      rol-verdict `PASS`, $0,43, 20 turns, auth via `CLAUDE_CODE_OAUTH_TOKEN`.
      De allowlist bevat `Bash(openspec validate *)` voor builder, reviewer en
      security (`worker/settings/*.json`), en de CLI staat in de image.
      **Nog niet waargenomen**: een rol die het commando in een run daadwerkelijk
      uitvoert — deze run had geen diff (de branch was identiek aan main), dus er
      viel niets te valideren. Dat bewijs valt uit de eerstvolgende builder-run.
      (Oude regel:) Eindbewijs volgt uit de eerste dispatch op de nieuwe image-tag: een rol
      die `openspec validate` zélf draait en het resultaat in zijn run-output zet.
