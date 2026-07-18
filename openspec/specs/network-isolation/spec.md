# network-isolation Specification

## Purpose
TBD - created by archiving change add-cage. Update Purpose after archive.
## Requirements
### Requirement: Default-deny egress in de namespace

De namespace `agents` SHALL een default-deny egress-policy hebben die elke pod
zonder expliciete toestemming nul uitgaand verkeer geeft. Toegestane uitzonderingen
SHALL alleen gelden voor pods met het label `habitat/component: worker`.

#### Scenario: Niet-gelabelde pod heeft geen egress

- **WHEN** een pod zonder de worker-allow-policy egress probeert
- **THEN** wordt al zijn uitgaand verkeer geweigerd

#### Scenario: DNS blijft werken voor workers

- **WHEN** de default-deny actief is
- **THEN** kan een worker namen resolven via kube-dns

### Requirement: Domein-allowlist, CNI-native afgedwongen

Uitgaand verkeer van een worker SHALL beperkt zijn tot een expliciete
domein-allowlist, afgedwongen door de CNI (Cilium `toFQDNs`), zonder egress-proxy.
De allowlist SHALL bevatten: `*.anthropic.com` (incl. `api.anthropic.com`),
`*.github.com` + `*.githubusercontent.com`, `*.pypi.org` + `*.pythonhosted.org`,
en `*.npmjs.org`. Verkeer naar andere domeinen SHALL geweigerd worden.

#### Scenario: Toegestaan domein

- **WHEN** een worker `github.com` of `api.anthropic.com` over 443 benadert
- **THEN** slaagt de verbinding

#### Scenario: Niet-toegestaan domein

- **WHEN** een worker een domein buiten de allowlist benadert
- **THEN** wordt de verbinding door de CNI gedropt (geen response, time-out)

### Requirement: Egress observeerbaar voor audit

Toegestane en geweigerde egress-flows van een worker SHALL achteraf observeerbaar
zijn (Hubble), zodat elk uitgaand verzoek reconstrueerbaar is.

#### Scenario: Flow zichtbaar

- **WHEN** een worker een verbinding maakt of een verbinding gedropt wordt
- **THEN** is die flow terug te zien in de flow-observability van het cluster

### Requirement: Image-pulls vallen buiten de pod-policy

De egress-policy SHALL geen voorziening voor image-pulls (`ghcr.io`) bevatten, omdat
pulls door kubelet/containerd op de node gebeuren en niet onder de pod-egress vallen.

#### Scenario: Worker-image wordt gepulld

- **WHEN** een node de worker-image van GHCR pullt
- **THEN** verloopt dat buiten de pod-egress-policy om

