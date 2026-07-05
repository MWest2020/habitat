# Design — kooi

## De kooi in één plaatje

```
namespace: agents
┌────────────────────────────────────────────────────────────────┐
│  worker-Job (SA: role-<rol>)                                     │
│   egress toegestaan → CoreDNS:53   +   squid-proxy:3128          │
│   egress geweigerd  → al het andere (default-deny)              │
│        │                                   │                    │
│        ▼                                   ▼                    │
│   naamresolutie                    squid (domein-allowlist):     │
│                                    .anthropic.com, github-HTTPS, │
│                                    pypi, npm  → internet         │
│                                    access.log = egress-audit     │
└────────────────────────────────────────────────────────────────┘
  secrets (SOPS+age, decrypt-at-apply door orchestrator):
    anthropic-api-key           ← elke rol-SA mag deze referencen
    pat-node-<n>                ← alleen de bij die node horende Job
```

## Beslissingen

### FQDN-allowlist kan niet in NetworkPolicy → egress-proxy (clevere valkuil)
k3s draait standaard Flannel + de kube-router netpol-controller: L3/L4-only, geen
DNS/FQDN-policies. "Allowlist api.anthropic.com" is dus níet uitdrukbaar als
NetworkPolicy. De CDN-IP's roteren bovendien — `ipBlock`-CIDR's pinnen is
onhoudbaar. Boringste oplossing: één Squid-pod met een statische domein-allowlist;
de worker-netpol staat dan alleen CoreDNS + proxy toe. Bonus: de Squid access-log is
gratis egress-audit. (Alternatief was Cilium met `toFQDNs` — zwaarder bewegend deel
op een klein cluster; niet gekozen.)

### DNS moet expliciet open (clevere valkuil)
Een default-deny egress blokkeert ook 53/udp+tcp naar CoreDNS → álle naamresolutie
sterft nog vóór het CDN-probleem. CoreDNS wordt gematcht via
namespaceSelector + podSelector (`k8s-app: kube-dns`) in `kube-system`, niet via de
ClusterIP (netpol matcht pod-IP's, niet de kube-proxy-DNAT'te service-IP).

### Image-pulls policyen we niet
`ghcr.io`-pulls doet kubelet/containerd op de node, buiten de pod-netpol om. De
allowlist hoeft ghcr dus niet te bevatten en we verspillen er geen policy aan.

### Eén cluster-age-key, geen per-node age-key (clevere valkuil)
SOPS+age versleutelt bestanden-at-rest in git; de decryptie-identiteit leeft waar
gedecrypt wordt. Zodra een secret in een cluster-`Secret` staat is het een gewoon
object — "per node" is dan betekenisloos. Node-intrekbaarheid hoort dus uit
per-node PAT-secrets + RBAC te komen, niet uit age. Eén cluster-age-key (privékey
alleen op de orchestrator-host = kroonjuweel), orchestrator doet
`sops -d | kubectl apply -f -`. Alleen `data`/`stringData` versleuteld, YAML blijft
diffbaar.

### Minimale RBAC
Eén SA per rol; elke rol-SA mag alleen zijn eigen node-PAT-secret + het
API-key-secret referencen, geen cluster-scope. Orchestrator-SA: Jobs CRUD in
`agents` + logs lezen, verder niets — geen vreemde secrets, geen andere namespaces.

## Wat deze change NIET doet
- Geen Job-manifest / dispatch — dat is `add-dispatch`.
- Geen aanmaak van de PAT's/age-key zelf (dat is bootstrap-handwerk van Mark); de
  change levert de structuur, `.sops.yaml`, en de mount-afspraken.

## Verificatie (DoD)
- `kubectl apply -k` zet namespace + proxy + policies.
- Egress-test vanuit een pod: alleen allowlist-domeinen bereikbaar, de rest faalt.
- RBAC-test: orchestrator-SA kan geen vreemd secret of andere namespace lezen.
