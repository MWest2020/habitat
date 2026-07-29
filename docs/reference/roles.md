---
status: draft
last_reviewed: 2026-07-29
---

# Rollen-referentie

Feiten over de vier worker-rollen (change `add-role-architecture`). Elke rol
draait als headless `claude -p` met `--permission-mode dontAsk` plus een
per-rol settings-JSON (`worker/settings/<rol>.json`): deny-by-default, alles
buiten de allowlist wordt geweigerd. De output is verplicht JSON volgens
`worker/schemas/<rol>.json`. Roldefinities leven als
`.claude/agents/<rol>.md` in de dóelrepo (sjabloon: `templates/agents/`),
skills als `.claude/skills/` (sjabloon: `templates/skills/`).

## Overzicht

| Rol | Doel | Schrijft code | Skill |
|---|---|---|---|
| `architect` | verkent read-only, levert een plan als structured output | nee | `plan-format` |
| `builder` | implementeert de change binnen het plan, levert bewijs | ja | `verify` |
| `reviewer` | adversarial review van de builder-branch in verse context | nee | `review-checklist` |
| `security` | security-review van de diff (afgeleid van anthropics/claude-code-security-review) | nee | `security-review` |

## Allowlist en deny per rol

**architect / reviewer / security** (identieke settings):

- Allow: `Read`, `Grep`, `Glob`, `Bash(git diff|log|status|show …)`.
- Deny: `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`,
  `Bash(git push …)`, en secrets-paden (`.env`, `**/secrets/**`,
  `**/*.pem`, `id_rsa*`).
- Extra voor architect: wijzigt de run tóch de working tree, dan draait de
  entrypoint dat terug en faalt de run (`worker/entrypoint.sh`, stap 4c).

**builder**:

- Allow: bovenstaande leestools plus `Edit`, `Write`, git-werkcommando's
  (`add`, `commit`, `rm`, `mv`, `checkout`, `branch`), test-/buildrunners
  (`uv run`, `uvx`, `npm test|run|ci`, `npx`, `go test|build|vet`, `make`,
  `pytest`, `shellcheck`) en basis-bestandscommando's (`mkdir`, `ls`, `cat`,
  `chmod`, `mv`, `cp`, `rm`).
- Deny: `git push` (pushen doet de entrypoint), netwerk (`curl`, `wget`,
  `ssh`, `scp`, `WebFetch`, `WebSearch`), infra (`kubectl`, `docker`) en
  dezelfde secrets-paden.
- Alleen de builder heeft hooks: een PreToolUse-guard
  (`pretooluse-guard.sh`, blokkeert hard) en een Stop-hook
  (`stop-verify.sh`, verificatie-gate vóór de run mag eindigen).

Alle rollen hebben `disableBypassPermissionsMode: "disable"`:
`bypassPermissions` is per settings-bestand onmogelijk gemaakt.

## Output-schema (kort)

Elk schema eist minimaal `verdict` (`PASS`/`FAIL`) en `summary`;
`additionalProperties: false`.

| Rol | Verplicht daarnaast | Inhoud |
|---|---|---|
| `architect` | `plan` | per buildertaak `objective`, `files`, `steps`, `verification` (+ optioneel `out_of_scope`, `risks`) |
| `builder` | `evidence` | testuitvoer/exitcodes als bewijs (+ optioneel `changes`, `deviations`) |
| `reviewer` | `findings` | per finding `severity` (`blocking`/`major`/`minor`), `location`, `description` |
| `security` | `findings` | zelfde vorm als reviewer |

## Verdicts sturen de keten

Het rol-verdict is een gate, geen rapport. De entrypoint leest `verdict` uit
de structured output; bij `FAIL` wordt de run als mislukt gemarkeerd, exit de
pod met code 1 en faalt de K8s-Job — de keten
(architect → builder → reviewer → security) stopt daar en een mens kijkt
ernaar. Reviewer en security geven FAIL bij ≥1 blocking finding; security
ook bij elk gevonden geheim.

## Twee verdedigingslagen

1. **Permissions** (settings-allowlist + `dontAsk` + hooks) — laag twee,
   niet de enige verdediging: er is een bekende historische bug waarbij
   deny-rules niet werden afgedwongen (research.md E).
2. **Container/Cilium** — de buitenste grens: non-root pod zonder
   capabilities, `automountServiceAccountToken: false`, en een
   Cilium-egress-allowlist als netwerkgrens.

## Bewuste afwijking: geen `--bare`

De research adviseert `claude --bare` voor reproduceerbaarheid, maar `--bare`
slaat de subscription-login over ("Not logged in", lokaal bewezen
2026-07-29) en habitat is sub-first. Determinisme komt daarom van `dontAsk`
plus expliciete settings plus het gepinde worker-image
(`worker/entrypoint.sh`, stap 1a).
