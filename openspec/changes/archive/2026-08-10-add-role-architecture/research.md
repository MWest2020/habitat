# Research — Anthropic-aanbevelingen voor multi-agent architecturen (2026-07-29)

Webresearch op officiële Anthropic-bronnen, uitgevoerd door een
research-agent in opdracht van de hub-sessie; per claim een bron-URL.
Context: habitat draait per rol een headless `claude -p`-run in een K8s
Job (nu builder/reviewer/security; architect komt erbij).

## A. Samenvatting

1. Anthropic's kernadvies: gebruik voorspelbare **workflows** (prompt
   chaining, routing, orchestrator-workers) boven autonome agents waar de
   taakstructuur vooraf bekend is — precies wat habitat met vaste rollen
   per K8s Job doet (building-effective-agents).
2. Subagents/rollen krijgen elk een **eigen system prompt, eigen toolset
   en eigen permissions**; Anthropic's eigen built-in rollen (Explore,
   Plan) zijn strikt read-only: "Write and Edit are denied" (sub-agents).
3. Permissions worden **deny → ask → allow** geëvalueerd; deny wint
   altijd, en `dontAsk`-mode is expliciet "useful for locked-down CI
   runs": alles buiten de allowlist wordt geweigerd (permissions,
   headless).
4. Voor headless/CI: `claude -p --bare` ("the same result on every
   machine") met expliciete `--allowedTools`, `--settings`, `--agents` en
   `--output-format json` (+ `--json-schema` voor gestructureerde output).
5. **Hooks zijn deterministisch waar prompts advisory zijn**: PreToolUse
   (exit 2 / `permissionDecision: "deny"`) blokkeert tool-calls hard; een
   Stop-hook is een verificatie-gate die de run pas laat eindigen als
   tests/build slagen.
6. Kwaliteitsprincipe: "Give Claude a check it can run" — zonder
   verifieerbaar signaal is "looks done" het enige stopcriterium
   (best-practices).
7. Reviews in een **verse context**: "A fresh context improves code
   review since Claude won't be biased toward code it just wrote".
8. Security: officieel `/security-review`-command en de
   `anthropics/claude-code-security-review` GitHub Action (AI-SAST met
   false-positive-filtering); officieel caveat: "niet gehardened tegen
   prompt injection", alleen voor trusted PRs.
9. Sandboxing (bubblewrap/Seatbelt) + netwerk-allowlist is de
   OS-afdwinglaag naast permissions; `--dangerously-skip-permissions`
   alleen in geïsoleerde containers.
10. Certificering heet **"Claude Certified …"** (Associate/Architect/
    Developer; Foundations + Architect-Professional). "Certified Claude
    Code Architect" bestaat niet onder die naam; curriculum dekt Claude
    Code, Agent SDK, Claude API en MCP; detail-syllabus achter het
    Claude Partner Network.

## B. Per rol: aanbevolen allowlist en skills

Eerlijkheid vooraf: Anthropic publiceert géén officiële per-rol
allowlist voor architect/builder/reviewer/security; onderstaande is een
synthese van officiële bouwstenen (Explore/Plan read-only, het
`security-reviewer`-voorbeeld, permission-syntax).

### B1. Architect / planner

Sjabloon = Anthropic's Plan-agent: "read-only tools; Write and Edit are
denied" (sub-agents). Workflow: "Explore first, then plan, then code"
(best-practices).

- Allowlist: `Read`, `Grep`, `Glob`; optioneel `Bash(git log *)`,
  `Bash(git diff *)` (prefix-syntax: permissions-doc). Geen Edit/Write.
- Headless: `claude --bare -p … --allowedTools "Read,Grep,Glob"
  --permission-mode dontAsk --output-format json --json-schema <plan>`.
- Skill: `plan-format` — beste specs zijn "self-contained: they name the
  files and interfaces involved, state what is out of scope, and end
  with an end-to-end verification step" (best-practices).
- Orchestratie-les: geef subtaken "an objective, an output format,
  guidance on the tools and sources to use, and clear task boundaries"
  (multi-agent-research-system).

### B2. Reviewer

Writer/Reviewer in gescheiden sessies, adversarial review in verse
context; "Report gaps, not style preferences" (best-practices).

- Allowlist: `Read`, `Grep`, `Glob`. Headless-tip: **diff via stdin**
  ("Piping the diff means Claude doesn't need Bash permission to read
  it") — dan kan Bash geheel weg. Anders alleen `Bash(git diff *)`,
  `Bash(git log *)`.
- Output: `--output-format json` + findings/severity-schema.
- Skill: review-checklist met repo-conventies.

### B3. Security-review

Officieel product: `/security-review` + GitHub Action
`anthropics/claude-code-security-review` — injection (SQL/command/XXE),
auth/IDOR, hardcoded secrets, crypto, RCE/deserialisatie, XSS;
false-positive-filtering; aanpasbaar via
`custom-security-scan-instructions`. Anthropic ving er intern pre-merge
een RCE (DNS rebinding) en een SSRF mee af (blog).

- Allowlist: `Read`, `Grep`, `Glob` (het officiële voorbeeld gebruikt
  ook Bash + `model: opus`; in habitat kan Bash weg of scoped).
- Skill: kopie van `.claude/commands/security-review.md` uit de
  Anthropic-repo, gecustomized ("Edit voor organization-specific
  requirements").
- Officieel caveat: niet gehardened tegen prompt injection → alleen
  trusted input.

### B4. Builder

- Allowlist (afgeleid): `Read`, `Edit`, `Write`, `Glob`, `Grep`, scoped
  `Bash(npm test *)`/`Bash(uv run *)`-achtigen, `Bash(git add *)`,
  `Bash(git commit *)`; **deny** `Bash(git push *)`, `Read(./.env)`,
  secrets-paden. Caveats uit de permissions-doc: één `*` matcht ook
  spaties; shell-operators worden per subcommand gematcht; runners als
  `npx`/`docker exec` worden niet gestript.
- Guardrails: verificatiecriteria in de prompt + bewijs eisen ("show
  evidence rather than asserting success"); PreToolUse-hook (exit 2 /
  deny) voor harde grenzen; Stop-hook "runs your check as a script and
  blocks the turn from ending until it passes" (max 8 blocks); "Unlike
  CLAUDE.md instructions which are advisory, hooks are deterministic."
- Sandboxing: OS-niveau (bubblewrap + socat op Linux); in unprivileged
  containers is `enableWeakerNestedSandbox` nodig → dan is de container
  zelf de isolatiegrens. `bypassPermissions` "only in isolated
  environments like containers or VMs".
- Skills: run/verify-skills; `disable-model-invocation: true` voor
  side-effect-skills; `allowed-tools`/`disallowed-tools` per skill.
- Agent-frontmatter (voor `--agents`/`.claude/agents/*.md`): `description`,
  `prompt`, `tools`, `disallowedTools`, `model`, `permissionMode`,
  `hooks`, `maxTurns`, `skills`, `memory`.

## C. Top-5 aanbevelingen voor habitat

1. **Deny-by-default per Job:** `claude --bare -p` +
   `--permission-mode dontAsk` + per-rol settings-JSON met
   `permissions.allow`; `disableBypassPermissionsMode: "disable"` voor
   niet-builder-rollen.
2. **Rollen als versiebeheerde agent-definities** met `tools`, `model`,
   `permissionMode`, `skills` — onderzoeksrollen strikt read-only.
3. **Deterministische gates met hooks:** PreToolUse voor secrets/push,
   Stop-hook draait de testsuite als exit-gate; adversarial review in
   verse context vóór "done".
4. **Container = isolatiegrens + egress-allowlist** (K8s NetworkPolicy
   als equivalent van sandbox `allowedDomains`); brede domeinen (bv.
   `github.com`) zijn potentiële exfiltratiepaden.
5. **Structured output + kleine evals:** per rol `--output-format json
   --json-schema` (+ `total_cost_usd` voor kosten), eval-set van ±20
   taken met end-state-evaluatie en LLM-as-judge.

## D. Certificering

Officieel programma via Pearson VUE: **CCAO-F** (Associate Foundations),
**CCAR-F** (Architect Foundations), **CCAR-P** (Architect Professional),
**CCDV-F** (Developer Foundations). CCAR-F dekt Claude Code, Agent SDK,
Claude API en MCP; $125, 120 min, slaaggrens 720/1000 (deels secundaire
bron). Gedetailleerd exam-blueprint niet publiek (Partner Network);
`anthropic.com/learn/certifications` gaf 404.

## E. Eerlijkheidsnotities

- Geen officiële per-rol allowlist-publicatie; sectie B is synthese.
- "Idempotent" komt in de docs niet voor; dichtstbijzijnd vocabulaire:
  `--bare` (reproduceerbaarheid), `dontAsk` (deterministisch), hooks
  ("deterministic" vs "advisory"), end-state-evaluatie.
- Secundair gemeld: historische bug waarbij deny-rules niet werden
  afgedwongen (claude-code issue #6699, v1.0.93) → deny-rules altijd
  combineren met OS-/container-enforcement (dat is ook de officiële lijn).

## F. Bronnen

Officiële docs (code.claude.com): sub-agents · permissions · skills ·
hooks · headless · sandboxing · best-practices.
Engineering/nieuws: anthropic.com/engineering/building-effective-agents ·
anthropic.com/engineering/multi-agent-research-system ·
claude.com/blog/automate-security-reviews-with-claude-code ·
github.com/anthropics/claude-code-security-review.
Certificering: pearsonvue.com/us/en/anthropic.html ·
anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification ·
(secundair) freeCodeCamp-prep-artikel.
Secundair ter signalering: github.com/anthropics/claude-code/issues/6699.
