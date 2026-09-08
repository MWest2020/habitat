## ADDED Requirements

### Requirement: Toegestane testrunners zitten in de image

Elk commando dat een rol-allowlist toestaat als test- of buildrunner SHALL in de
worker-image aanwezig zijn. Een toegestaan maar ontbrekend commando is erger dan
een verboden commando: een `verify.sh` die de runner alleen "indien aanwezig"
aanroept, degradeert dan stil tot een no-op en de run meldt groen voor een
controle die niet gedraaid heeft.

#### Scenario: shellcheck is aanroepbaar in de kooi

- **WHEN** een builder-run `shellcheck` aanroept op een shellscript in de doelrepo
- **THEN** draait shellcheck echt en geeft hij zijn bevindingen terug, in plaats
  van te falen op een ontbrekend commando of overgeslagen te worden
