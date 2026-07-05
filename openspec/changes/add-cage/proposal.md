## Why

Een worker die alles mag wat de container mag, is geen platform maar een risico.
De kooi is wat Habitat een platform maakt: een agent-Job kan alleen bij de plekken
die expliciet zijn toegestaan, alleen bij de secrets die bij zijn rol horen, en zijn
credentials zijn per node in te trekken. Zonder de kooi valt er niets veilig te
draaien; met de worker-image (`add-worker-image`) erbij is dit het tweede
fundament dat de rest (dispatch, audit) veronderstelt.

## What Changes

- **Namespace `agents`** als Kustomize-base, expliciet, geen Helm.
- **Egress-proxy (Squid)** met een statische domein-allowlist, want k3s draait
  Flannel + kube-router (L3/L4-only) en kan geen FQDN-policies. Al het uitgaand
  verkeer van workers loopt via deze ene proxy.
- **Default-deny egress-NetworkPolicy**: een worker mag alleen naar CoreDNS (53) en
  de proxy (3128). Eén egress-pad; ook git-over-HTTPS loopt door de proxy.
- **RBAC**: een ServiceAccount per rol (minimaal) en een orchestrator-SA die alleen
  Jobs mag CRUD'en in `agents` en logs mag lezen. Elke rol-SA mag alleen de eigen
  node-PAT-secret en het API-key-secret referencen.
- **SOPS+age** met één cluster-age-key: secrets versleuteld-at-rest in git, de
  orchestrator decrypt-at-apply. Node-intrekbaarheid via per-node PAT-secrets + RBAC.

## Capabilities

### New Capabilities

- `network-isolation`: default-deny egress met precies twee toegestane bestemmingen
  (CoreDNS + proxy) en een auditeerbare domein-allowlist in de proxy.
- `rbac-isolation`: minimale ServiceAccounts per rol en een strak begrensde
  orchestrator-SA; geen toegang tot vreemde secrets of namespaces.
- `secret-management`: SOPS+age met één cluster-age-key, decrypt-at-apply, en
  per-node PAT-secrets die per node intrekbaar zijn.

### Modified Capabilities

<!-- Geen: er bestaan nog geen specs. -->

## Impact

- Levert de namespace, proxy, policies en secret-structuur waarin de workers uit
  `add-worker-image` draaien en waarop `add-dispatch` Jobs plaatst.
- Legt vast dat `HTTPS_PROXY`/`NO_PROXY` in workers gezet worden (de worker-image
  veronderstelt dit al).
- De egress-allowlist bevat github + anthropic + pypi + npm; image-pulls (ghcr.io)
  lopen buiten de pod-netpol om (kubelet/containerd) en worden niet gepolicyed.
