# Design — kooi

## De kooi in één plaatje

```
namespace: agents   (kubeadm-cluster, Cilium v1.19 CNI, Hubble aan)
┌────────────────────────────────────────────────────────────────┐
│  worker-Job (label habitat/component=worker, SA role-<rol>)      │
│    default-deny egress (k8s NetworkPolicy, alle pods)            │
│    + CiliumNetworkPolicy toFQDNs:                                │
│        DNS → kube-dns    (Cilium DNS-proxy leert FQDN→IP)        │
│        443 → .anthropic.com, .github.com, .githubusercontent,    │
│              pypi/pythonhosted, npmjs   → internet               │
│        al het andere → gedropt door de CNI                       │
└────────────────────────────────────────────────────────────────┘
  audit: Hubble flow-logs (draait al)      geen proxy, geen sidecar
  secrets (SOPS+age, decrypt-at-apply door orchestrator):
    anthropic-api-key   ← elke rol-Job mag deze mounten
    pat-node-<n>        ← alleen de bij die node horende Job
```

## Beslissingen

### Cilium `toFQDNs` i.p.v. een egress-proxy (gecorrigeerde aanname)
Het oorspronkelijke ontwerp koos een Squid-proxy omdat aangenomen werd dat het
cluster k3s + kube-router draaide (L3/L4-only, geen FQDN-policy). Het cluster blijkt
echter **kubeadm met Cilium v1.19** — dat heeft `CiliumNetworkPolicy` met `toFQDNs`,
precies de DNS-bewuste domein-allowlist die we wilden. Daarmee is de proxy
overbodige complexiteit: de allowlist is één policy in de CNI, geen extra pod,
config, of `HTTPS_PROXY`-plumbing. De clevere valkuil zou zijn een proxy bolt-on te
houden terwijl de CNI het native kan.

### DNS moet expliciet, en de DNS-proxy is de sleutel
`toFQDNs` werkt doordat Cilium de DNS-requests onderschept en zo FQDN→IP leert. De
policy staat daarom DNS naar kube-dns toe met `rules.dns: matchPattern "*"`; zonder
die regel leert Cilium geen IP's en valt alles dicht.

### Default-deny voor de hele namespace, niet alleen workers
Een namespace-brede k8s `NetworkPolicy` (default-deny egress, `podSelector: {}`)
zorgt dat élke pod zonder expliciete allow nul egress heeft; de Cilium-policy voegt
alleen voor workers de allowlist toe. Policies zijn additief (whitelist-union), dus
een niet-gelabelde pod houdt nul egress.

### Egress-audit uit Hubble
Hubble (relay + ui) draait al in het cluster. Daarmee zijn toegestane én gedropte
flows per pod zichtbaar — de audit die de Squid access-log zou leveren, hebben we
dus gratis en fijnmaziger.

### Eén cluster-age-key, geen per-node age-key (ongewijzigd)
SOPS+age versleutelt bestanden-at-rest in git. Zodra een secret een cluster-`Secret`
is, is "per node" betekenisloos. Node-intrekbaarheid komt dus uit per-node
PAT-secrets + RBAC, niet uit age. Eén cluster-age-key (privé alleen op de
orchestrator-host), decrypt-at-apply. Alleen `data`/`stringData` versleuteld.

### Minimale RBAC
Rol-SA's krijgen géén API-token (`automountServiceAccountToken: false`) en nul
rechten — een worker praat nooit met de kube-API. Orchestrator-SA: Jobs CRUD in
`agents` + logs lezen, verder niets. Secret-uitrol gebeurt met een admin-kubeconfig,
niet met de orchestrator-SA.

## Wat deze change NIET doet
- Geen Job-manifest / dispatch — dat is `add-dispatch`.
- Geen aanmaak van de PAT's/age-key zelf (bootstrap-handwerk van Mark); de change
  levert de structuur, `.sops.yaml`, en de mount-afspraken.

## Verificatie (live uitgevoerd 2026-07-05)
- `kubectl apply -k cage/`: namespace + policies + RBAC aangemaakt, CNP `VALID=True`.
- Egress-test (worker-gelabelde pod): `github.com`→200, `api.anthropic.com`→404
  (verbinding toegestaan), `example.com`→timeout, curl-exit 28 (gedropt). DNS werkt.
- RBAC-test (`auth can-i` als orchestrator-SA): jobs/logs in `agents` = ja; secrets,
  kube-system, andere namespaces, cluster-scope = nee.
