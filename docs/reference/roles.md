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
  `pytest`, `shellcheck`), `openspec validate` en `mkdir`, `ls`, `chmod`.
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
   parse-/logicafout wordt de tool geweigerd, niet toegestaan. Uitzondering:
   een rol mag zijn eigen roldefinitie **lezen** — `Read` op
   `.claude/agents/<rol>.md` — omdat de worker elke rol opdraagt die te volgen;
   de rest van `.claude/` (credentials, settings) blijft dicht, `Edit`/`Write`
   op `.claude/` ook, en een symlink in dat pad wordt geweigerd.
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

## OpenSpec-CLI in de image

De image bevat `@fission-ai/openspec` (gepind; let op: het kale `openspec` op npm
is een lege placeholder). Builder, reviewer en security mogen precies één
subcommando draaien: `openspec validate *`. Muterende subcommando's — met name
`openspec archive`, dat mappen verplaatst — blijven geweigerd door de
deny-by-default-laag; archiveren is een besluit, geen bouwstap. De architect heeft
de regel niet: die plant en heeft geen artefact om te valideren.

Zonder deze twee dingen samen (CLI **en** allowlist-regel) kan een rol de
validatie-taak van een change niet uitvoeren en verschuift het bewijs naar een mens
— waargenomen op een builder-run die daarop terugviel op FAIL terwijl het werk af
was.

## Skills: gepind in de image, per rol gematerialiseerd

De image draagt de skill-bodies uit skill-forge, gepind op een commit
(`ARG SKILLS_REF` in de Containerfile) — nooit een branch, zodat een skill-update
een zichtbare pin-bump is en draaiende runs niet verschuiven.

Bij een run leest de entrypoint het rolbestand van de doelrepo
(`.claude/agents/<rol>.md`) en kopieert **alleen** de skills uit zijn
`skills:`-regel naar `~/.claude/skills/`. Alle skills aanbieden zou ≈ 4.000 tokens
per run kosten aan beschrijvingen (44 in het register, gemiddeld 91 per skill),
terwijl een rol er nul of één noemt.

Namen moeten een slug zijn (`a-z0-9-`); iets als `../../etc` wordt geweigerd met
een melding. Een skill die niet in de image zit wordt gemeld en overgeslagen — een
ontbrekende skill laat bouwwerk niet mislukken.

Uit hetzelfde rolbestand komt `model:`, dat als `--model` aan de agent-run wordt
meegegeven. Ontbreekt het veld, dan draait de run zoals voorheen.

## Wat de allowlist wél en niet is

De builder mag testrunners draaien (`make`, `npm test|run`, `uv run`, `pytest`,
`go test`). Die voeren **code uit de doelrepo** uit — een `Makefile`-target, een
`package.json`-script, een `conftest.py`. Dat is inherent aan bouwen en testen: je
kunt geen tests draaien zonder repo-code te draaien.

De allowlist is dus **geen sandbox**. Hij houdt tegen wat een agent per ongeluk of
achteloos doet (`curl`, `kubectl`, `cat .env`), niet wat een vastberaden agent via
zijn eigen testcode doet. De echte grenzen liggen een laag lager: de container, de
egress-allowlist, geen `GIT_PAT` in het agentproces, en `git` die geen repo-hooks
draait (`core.hooksPath=/dev/null`).

Wat er bewust **niet** in staat: `uvx` en `npx`. Die halen een willekeurig pakket
van internet en voeren het uit — een andere klasse dan "draai de tests van deze
repo", en npm/PyPI staan in de egress-allowlist.
