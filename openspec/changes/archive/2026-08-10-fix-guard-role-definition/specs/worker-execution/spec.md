## ADDED Requirements

### Requirement: Tool-guard schermt credentials af, niet de rol-definitie

De PreToolUse-guard (tweede verdedigingslaag) SHALL secret- en
credential-paden weigeren voor alle rollen — minimaal `.credentials.json`,
`/var/run/claude/`, `/secrets/`, `.env`, `*.pem`, `id_rsa`, `/proc/` en
`/sys/` — ongeacht de allowlist, en SHALL faalt-dicht zijn (bij een parse- of
logicafout: weigeren).

De guard SHALL het **lezen** van de rol-definitie
`.claude/agents/<rol>.md` in de doelrepo toestaan, omdat de worker elke rol
opdraagt die te volgen. Deze uitzondering SHALL alléén gelden voor `Read` en
alléén voor paden die eindigen op `.claude/agents/<naam>.md`; `Edit`, `Write`
en `NotebookEdit` op `.claude/` SHALL geweigerd blijven, en alle overige
credential-/secret-paden onder `.claude/` (zoals `.credentials.json`) SHALL
geweigerd blijven.

#### Scenario: Rol leest zijn eigen definitie

- **WHEN** een rol `Read` aanroept op `.claude/agents/architect.md` in de doelrepo
- **THEN** staat de guard de lezing toe
- **AND** kan de rol de instructie volgen zonder de hook te omzeilen

#### Scenario: Credentials blijven dicht

- **WHEN** een tool een credential-pad raakt (`.claude/.credentials.json`,
  `/var/run/claude/…`) of een secret-pad (`.env`, `*.pem`, `id_rsa`, `/secrets/`)
- **THEN** weigert de guard, ook als het pad onder `.claude/` valt

#### Scenario: Schrijven naar de rol-definitie geweigerd

- **WHEN** een rol `Edit` of `Write` aanroept op `.claude/agents/<rol>.md`
- **THEN** weigert de guard (de uitzondering geldt alleen voor lezen)
