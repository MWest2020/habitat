## Why

Een worker die alles mag wat de container mag, is geen platform maar een risico.
De kooi is wat Habitat een platform maakt: een agent-Job kan alleen bij de plekken
die expliciet zijn toegestaan, alleen bij de secrets die bij zijn rol horen, en zijn
credentials zijn per node in te trekken. Zonder de kooi valt er niets veilig te
draaien; met de worker-image (`add-worker-image`) erbij is dit het tweede
fundament dat de rest (dispatch, audit) veronderstelt.

## What Changes

- **Namespace `agents`** als Kustomize-base, expliciet, geen Helm.
- **Default-deny egress** (namespace-brede k8s NetworkPolicy) + een
  **CiliumNetworkPolicy met `toFQDNs`** die precies de toegestane domeinen toestaat.
  Het cluster draait Cilium (v1.19), dus domein-allowlisting is CNI-native — géén
  egress-proxy nodig. Egress-audit komt uit Hubble (draait al).
- **RBAC**: een ServiceAccount per rol (minimaal, zonder API-token) en een
  orchestrator-SA die alleen Jobs mag CRUD'en in `agents` en logs mag lezen.
- **SOPS+age** met één cluster-age-key: secrets versleuteld-at-rest in git, de
  orchestrator decrypt-at-apply. Node-intrekbaarheid via per-node PAT-secrets + RBAC.

## Capabilities

### New Capabilities

- `network-isolation`: default-deny egress met een auditeerbare domein-allowlist,
  CNI-native afgedwongen (Cilium `toFQDNs`); alleen allowlist-domeinen + DNS bereikbaar.
- `rbac-isolation`: minimale ServiceAccounts per rol en een strak begrensde
  orchestrator-SA; geen toegang tot vreemde secrets of namespaces.
- `secret-management`: SOPS+age met één cluster-age-key, decrypt-at-apply, en
  per-node PAT-secrets die per node intrekbaar zijn.

### Modified Capabilities

<!-- Geen: er bestaan nog geen specs. -->

## Impact

- Levert de namespace, policies en secret-structuur waarin de workers uit
  `add-worker-image` draaien en waarop `add-dispatch` Jobs plaatst.
- Workers hebben géén proxy-plumbing nodig: egress is direct maar CNI-gefilterd op
  FQDN. Workers dragen het label `habitat/component: worker` zodat de policy hen selecteert.
- De egress-allowlist bevat github + anthropic + pypi + npm; image-pulls (ghcr.io)
  lopen buiten de pod-policy om (kubelet/containerd) en worden niet gepolicyed.
