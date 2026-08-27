## Why

De boomhuis-communicatielaag wil straks een doel dat in een kanaal ontstaat
(bijv. "@bouwer maak change X") kunnen doorgeven aan een habitat-run — de
doel→dispatch-brug (boomhuis `add-habitat-bridge`, fase 3). Vandaag kan dat niet:
de worker leest zijn opdracht volledig uit env-vars en gebruikt "geen andere
invoerkanalen" (`worker-execution`). Er is dus geen plek voor een taaktekst, een
architect-plan of reviewer-findings behalve de zes vaste env-strings.

Dit amendeert dat invariant op de **enige** manier die de kooi niet verzwakt:
een optionele taak-referentie die een **git-pad** is. De worker leest de taak uit
een bestand in de gecloonde doelrepo — dus nog steeds alleen uit env + git, geen
socket, geen live kanaal, geen relay-egress. De reproduceerbaarheid ("elke run
reconstrueerbaar uit zijn Job-spec + git") blijft volledig overeind.

## What Changes

- **`worker-execution`**: het "Env-interface"-requirement krijgt een **optionele**
  `HABITAT_TASK_REF` — een pad (relatief aan de doelrepo-root) naar een
  taak/context-bestand dat de worker ná de checkout mag lezen als extra context
  bij de rol-run. Afwezig = gedrag exact als nu. De regel "geen andere
  invoerkanalen dan env + git" blijft: de taak-ref is git, geen nieuw kanaal.
- **`worker/entrypoint.sh`** (apply): als `HABITAT_TASK_REF` gezet is en het pad
  binnen de repo bestaat, wordt de inhoud als context aan de prompt toegevoegd;
  een pad buiten de repo of een niet-bestaand bestand → fail-closed (exit, geen
  run), zoals bij een ontbrekende verplichte env.

## Capabilities

### Modified Capabilities

- `worker-execution`: optionele git-pad-taak-referentie als extra invoer, binnen
  het bestaande "alleen env + git"-invariant.

### New Capabilities

<!-- Geen. -->

## Impact

- Raakt **niet** de kooi: geen wijziging aan NetworkPolicies/CiliumNetworkPolicies,
  RBAC, Job-templates, of de egress-allowlist. Workers krijgen geen relay-toegang
  en geen extra netwerk.
- `worker/entrypoint.sh` leest bij aanwezige `HABITAT_TASK_REF` één bestand uit de
  al-gecloonde repo; pad-begrenzing (binnen de repo) is een harde check.
- Enables (los, proposal-first daar): boomhuis `add-habitat-bridge` — de
  orchestrator schrijft een taakbestand in de doelrepo (git) en geeft het pad mee
  als `HABITAT_TASK_REF`. Mark blijft poortwachter van elke dispatch.
