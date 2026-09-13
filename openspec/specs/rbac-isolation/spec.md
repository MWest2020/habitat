# rbac-isolation Specification

## Purpose

Wat een rol in het cluster mag: een eigen ServiceAccount per rol, zo klein
mogelijk.

Zonder dit deelt elke agent de rechten van de grootste agent, en dan is de
zwakste rol de effectieve grens. Eén SA per rol maakt "wat kan deze agent
aanrichten" een vraag met een antwoord.

De orchestrator-SA is apart en strakker begrensd genoemd, en dat is geen detail:
dat is de enige identiteit die Jobs kan maken. Een orchestrator die meer mag dan
dispatchen, is een agent die zichzelf meer kan geven.
## Requirements
### Requirement: ServiceAccount per rol, minimaal

Elke rol (builder, reviewer, security) SHALL een eigen ServiceAccount in de
namespace `agents` hebben. Een rol-SA SHALL geen cluster-scope-rechten hebben en
SHALL alleen het API-key-secret en het eigen node-PAT-secret mogen referencen.

#### Scenario: Rol-SA leest zijn eigen secrets

- **WHEN** een worker onder rol-SA `role-builder` draait
- **THEN** kan hij het API-key-secret en het bij zijn node horende PAT-secret mounten

#### Scenario: Rol-SA probeert een vreemd secret

- **WHEN** een rol-SA een secret buiten zijn toegewezen set probeert te lezen
- **THEN** wordt dat door RBAC geweigerd

### Requirement: Strak begrensde orchestrator-SA

De orchestrator-SA SHALL alleen Jobs mogen aanmaken, lezen, en verwijderen in de
namespace `agents` en pod-logs mogen lezen. De orchestrator-SA SHALL geen secrets
buiten de eigen mogen lezen, geen cluster-scope-rechten hebben, en geen toegang tot
andere namespaces hebben.

#### Scenario: Orchestrator dispatcht en leest logs

- **WHEN** de orchestrator een Job aanmaakt en de logs streamt in `agents`
- **THEN** slagen beide acties

#### Scenario: Orchestrator probeert buiten zijn scope

- **WHEN** de orchestrator-SA een secret leest of een resource in een andere
  namespace benadert
- **THEN** wordt dat door RBAC geweigerd

