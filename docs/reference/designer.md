---
status: draft
last_reviewed: 2026-11-21
---

# Designer-rol (add-designer-role)

Feiten over de zesde rol. Waarom zo, en wat er al bestond:
[designer-agent](../explanation/designer-agent.md). De roldefinitie is de
handbook-seed `docs/agents/seeds/designer.md` (fallback:
`templates/agents/designer.md`).

## Rol

Draait los, niet in de keten (zie [Dispatch](#dispatch)). De brief komt binnen
als `HABITAT_TASK_REF`; de levering staat op de run-branch onder `design/brand/`.

- **Allowlist:** `Read`, `Edit`, `Write`, `Grep`, `Glob`, git `add|commit|rm|mv|
  status|diff|log|show`, `mkdir`, `ls`, `design-kit *`, `design-check *`,
  `logo-tool *`, `playtest-shoot *`. **Deny:** die van de builder (netwerk,
  `git push`, `cp`/`mv`, secrets-paden) plus `npm`, `npx`, `uvx`, `pip`,
  `NotebookEdit`. Geen package-runners: de kooi haalt voor deze rol niets op.
- **Gereedschap in de image:** `rsvg-convert`; `design-kit` (render,
  text2path, contrast, fonts; venv met Pillow 12.0.0 en fontTools 4.60.1); de
  OFL-letters Nunito, Fredoka, Baloo 2, Lexend en Andika (google/fonts, gepind);
  `logo-tool` voor de scripts van de logo-design-skill (MIT, gepind, zonder de
  bibliotheek met logo's van derden), methode in `/opt/habitat/logo-design/`.
- **Gate:** `design-check design/brand` als Stop-hook
  (`worker/hooks/stop-design-check.sh`, blokkeert één keer) en daarna in de
  entrypoint: `env -u GIT_PAT HOME=/nonexistent worker/design-gate.sh`, met
  `python3 -I`. Die faalt ook op elk gewijzigd, verwijderd of nieuw pad buiten
  `design/brand/` (`--no-renames`, NUL-gescheiden). Faalt de gate, dan is de run
  `failed`, ook bij een PASS van de agent. Wat hij meet staat in
  [designer-agent](../explanation/designer-agent.md#what-the-gates-check-and-what-they-cannot).
- **Git in de entrypoint** (alle rollen, `worker/git-safe.sh`): geen system- of
  global-config, de nodige sleutels uit de omgeving, `.git/config` na de run
  teruggezet uit een kopie in het geheugen. Zo draait geen fsmonitor, filter of
  credential-helper die de agent schreef terwijl `GIT_PAT` gezet is.
- **Netwerk:** de rol heeft geen netwerk- en geen package-tools; de pod deelt de
  egress van de worker (Anthropic, GitHub, npm, PyPI), want clone en push
  gebeuren in dezelfde pod.
- **Schema:** `verdict`, `summary`, `evidence` (laatste `design-check`-uitvoer),
  `directions` (2-3: `id`, `name`, `idea`), `recommended`, `deliverables`,
  optioneel `deviations`.
- **Model:** `opus` in de seed: eenmalig merkwerk dat op het oog beoordeeld wordt
  (de uitzondering in de modelregel).

## Dispatch

De designer draait als losse rol, niet in `chain.sh`. De wrapper controleert
dat de brief op de default branch staat, dispatcht één run en opent bij succes
een **draft** PR vanaf de run-branch:

```
dispatch/designer.sh <owner/repo> <brief-pad> [label]
# bv.
WORKER_IMAGE=ghcr.io/mwest2020/habitat-worker:<sha> HABITAT_HANDBOOK_REF=<sha> \
KUBECTL="ssh -o BatchMode=yes jumpy kubectl" \
  dispatch/designer.sh MWest2020/bazibo docs/design/brand-brief.md
```

- `HABITAT_TASK_REF` = het brief-pad; de change-naam is het label (default
  `brand-<YYYYmmdd>`), alleen een naam voor branch en Job.
- `HABITAT_MAX_BUDGET_USD` default `15.00` in de wrapper; deadline 3600 s
  (zoals de builder). `DESIGNER_NO_PR=1` slaat de PR over.
- Geen geslaagde run, geen PR; de wrapper merget nooit. `<owner/repo>` en het
  brief-pad worden gevalideerd; het rapport van de agent gaat als platte tekst
  in een fenced block in de PR-body (geen mentions, links of HTML), max 20 kB.
- Vereist: de handbook-seed `docs/agents/seeds/designer.md` op
  `HABITAT_HANDBOOK_REF` (anders faalt de rol dicht), de ServiceAccount
  `role-designer` uit `cage/rbac.yaml` in het cluster, en een worker-image vanaf
  de commit die `worker/design/` bevat.

## Levering

Alles onder `design/brand/` in de doelrepo:

| Pad | Inhoud |
|---|---|
| `rationale.md` | `## Direction <id> <naam>` per richting (2-3) en `## Recommendation` |
| `directions/<id>/` | `mark.svg`, `tokens.json`, `preview.png` |
| `logo/` | `mark`, `wordmark`, `full-light`, `full-dark` (SVG + PNG); `mark-24.png`, `mark-96.png` |
| `icon/` | `play-512.png` (32-bit, opaak), `appstore-1024.png` (zonder alpha) |
| `adaptive/` | `foreground`, `background`, `monochrome` (SVG + 432x432 PNG = 108 dp op 4x) |
| `store/` | `feature-graphic` (1024x500), `screenshot-frame-nl`, `-en` (1080x1920); SVG + PNG zonder alpha |
| `tokens.json`, `tokens.css` | kleuren (base, ink, ink-soft, brand, on-brand, per groep accent/tint/text) en letters (families, scale_px, weights) |
| `LICENSES.md` | elke letter met de SIL OFL 1.1, en de licentie van het beeld (CC0-1.0 of MIT) |

Tests: `bash worker/test-design-check.sh` en `bash worker/test-git-safe.sh` (CI-stap
`worker-tests`).
