## ADDED Requirements

### Requirement: Secrets versleuteld-at-rest met SOPS+age

Alle secrets in de repo SHALL met SOPS+age versleuteld zijn; een onversleuteld
secret SHALL nooit gecommit worden. De versleuteling SHALL alleen de waarden
(`data`/`stringData`) betreffen zodat de YAML-structuur diffbaar blijft. Een
`.sops.yaml` met de creation-rules SHALL in de repo staan.

#### Scenario: Secret in git

- **WHEN** een secret naar de repo gecommit wordt
- **THEN** zijn de waarden versleuteld en de sleutels/structuur leesbaar
- **AND** staat er geen onversleutelde secret-waarde in de git-historie

### Requirement: Eén cluster-age-key, decrypt-at-apply

Er SHALL één cluster-age-key zijn waarvan de privékey alleen op de
orchestrator-host staat. De orchestrator SHALL secrets bij apply-tijd decrypten
(`sops -d | kubectl apply -f -`); er SHALL geen in-cluster decryptie-component zijn.

#### Scenario: Secret uitrollen

- **WHEN** de orchestrator een SOPS-versleuteld secret toepast
- **THEN** wordt het op de host gedecrypt en als cluster-Secret aangemaakt
- **AND** verlaat de age-privékey de orchestrator-host niet

### Requirement: Per-node PAT-secrets, per node intrekbaar

Er SHALL per node een eigen PAT-secret zijn (single-repo fine-grained PAT,
`contents:write`). Node-intrekbaarheid SHALL bereikt worden door dat node-PAT in te
trekken en het bijbehorende secret te verwijderen — niet via een per-node age-key.

#### Scenario: Node intrekken

- **WHEN** een node uit dienst gaat
- **THEN** wordt zijn PAT ingetrokken en zijn PAT-secret verwijderd
- **AND** kunnen Jobs op die node daarna niet meer bij de doelrepo
