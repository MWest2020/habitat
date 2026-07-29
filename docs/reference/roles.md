---
status: draft
last_reviewed: 2026-07-29
---

# Rollen-referentie

Feiten over de vier worker-rollen (change `add-role-architecture`). Elke rol
draait als headless `claude -p` met `--permission-mode dontAsk` plus een
per-rol settings-JSON (`worker/settings/<rol>.json`): deny-by-default. De
worker geeft `--setting-sources user` mee: settings en hooks uit de gekloonde
dóelrepo worden NIET geladen. De agent draait zonder `GIT_PAT` in de omgeving
(`env -u GIT_PAT`); clonen en pushen doet de entrypoint, zodat
repo-gecontroleerde code (Makefile, npm-scripts) niet geauthenticeerd kan
pushen. De output is verplicht JSON volgens `worker/schemas/<rol>.json`;
roldefinities leven als `.claude/agents/<rol>.md` in de dóelrepo, skills als
`.claude/skills/` (sjablonen: `templates/agents/`, `templates/skills/`).

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
- Deny: `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `git push`,
  secrets-/credential-paden (`.env`, `**/secrets/**`, `*.pem`, `id_rsa*`,
  `.credentials.json`).
- Architect extra: repo-wijzigingen draait de entrypoint terug en de run
  faalt (`worker/entrypoint.sh`, stap 4c).

**builder**:

- Allow: bovenstaande leestools plus `Edit`, `Write`, git-werkcommando's
  (`add`, `commit`, `rm`, `mv`, `checkout`, `branch`), test-/buildrunners
  (`uv run`, `uvx`, `npm test|run|ci`, `npx`, `go test|build|vet`, `make`,
  `pytest`, `shellcheck`) en `mkdir`, `ls`, `chmod`.
- Deny: `git push` (pushen doet de entrypoint), netwerk (`curl`, `wget`,
  `ssh`, `scp`, `nc`), infra (`kubectl`, `docker`), dezelfde secrets-paden.

Alle rollen hebben `disableBypassPermissionsMode: "disable"`. Alleen de
builder heeft de Stop-hook `worker/hooks/stop-verify.sh`: heeft de doelrepo
een `scripts/verify.sh`, dan moet die slagen vóór de run mag eindigen; het
script komt uit de basiscommit, dus de builder kan de gate niet ontwapenen.

## Output-schema (kort)

Elk schema eist minimaal `verdict` (`PASS`/`FAIL`) en `summary`;
`additionalProperties: false`.

| Rol | Verplicht daarnaast | Inhoud |
|---|---|---|
| `architect` | `plan` | per buildertaak `objective`, `files`, `steps`, `verification` (+ optioneel `out_of_scope`, `risks`) |
| `builder` | `evidence` | testuitvoer/exitcodes als bewijs (+ optioneel `changes`, `deviations`) |
| `reviewer` | `findings` | per finding `severity` (`blocking`/`major`/`minor`), `location`, `description` |
| `security` | `findings` | zelfde vorm als reviewer |

## Verdicts sturen de keten (fail-closed)

Het rol-verdict is een gate en fail-closed: alleen een expliciete `PASS` in
de structured output laat de run slagen. Bij `FAIL` óf een ontbrekend
machinaal verdict valt de gate dicht: pod-exit 1, de K8s-Job faalt, de keten
(architect → builder → reviewer → security) stopt en een mens kijkt ernaar.
Reviewer en security geven FAIL bij ≥1 blocking finding; security ook bij
elk gevonden geheim.

## Drie verdedigingslagen

1. **Permissions** — per-rol allowlist, deny-by-default via `dontAsk`. Niet
   de enige laag: er is een bekende historische bug waarbij deny-rules niet
   werden afgedwongen (research.md E).
2. **PreToolUse-guard** (`worker/hooks/pretooluse-guard.sh`) — draait bij
   ALLE vier de rollen, ongeacht de allowlist, en faalt dicht op push-,
   secrets- en credential-paden (ook via Bash-lezers); bij een
   parse-/logicafout wordt de tool geweigerd, niet toegestaan.
3. **Container + Cilium** — de buitenste grens: non-root pod zonder
   capabilities, per rol een eigen ServiceAccount zonder token of
   RBAC-rechten (`role-architect`/`role-builder`/`role-reviewer`/
   `role-security`, `automountServiceAccountToken: false`; `cage/rbac.yaml`),
   plus de Cilium-egress-allowlist als netwerkgrens.

## Netwerk: begrensd, niet geïsoleerd

Directe netwerktools worden bij elke rol geweigerd (`curl`, `wget`, `ssh`,
`WebFetch`, `WebSearch`), maar volledige isolatie is het niet: `npx`, `uvx`
en `uv run` halen bewust packages op van npm/PyPI en de builder kan
api.github.com bereiken — een geaccepteerd package-kanaal, begrensd door de
Cilium-egress-allowlist (`cage/ciliumnetworkpolicy.yaml`:
anthropic/github/pypi/npm-domeinen, alleen 443). Bekende restrisico's
(follow-up, buiten deze change): de DNS-regel `matchPattern: "*"` laat elke
DNS-query toe (DNS-exfiltratie mogelijk) en de runners kunnen arbitraire
code van die registries ophalen en draaien.

## Bewuste afwijking: geen `--bare`

De research adviseert `claude --bare`, maar dat slaat de subscription-login
over ("Not logged in", lokaal bewezen 2026-07-29) en habitat is sub-first.
Determinisme komt van `dontAsk` plus expliciete settings plus het gepinde
worker-image (`worker/entrypoint.sh`, stap 1a).
