## ADDED Requirements

### Requirement: Default-deny egress met twee toegestane bestemmingen

De namespace `agents` SHALL een default-deny egress-NetworkPolicy hebben. Een
worker-pod SHALL uitsluitend egress mogen naar CoreDNS (poort 53) en de
egress-proxy (poort 3128); al het overige uitgaand verkeer SHALL geweigerd worden.

CoreDNS SHALL gematcht worden via namespace- en pod-selector, niet via de ClusterIP.

#### Scenario: Verkeer naar de proxy is toegestaan

- **WHEN** een worker-pod een HTTP(S)-verzoek via de proxy stuurt
- **THEN** slaagt het verzoek

#### Scenario: Direct internetverkeer wordt geweigerd

- **WHEN** een worker-pod rechtstreeks (buiten de proxy om) een extern adres benadert
- **THEN** wordt de verbinding geweigerd

#### Scenario: DNS blijft werken

- **WHEN** de default-deny egress actief is
- **THEN** kan de worker namen resolven via CoreDNS op poort 53

### Requirement: Domein-allowlist in de egress-proxy

De egress-proxy SHALL een statische domein-allowlist afdwingen die precies de
benodigde bestemmingen bevat: `.anthropic.com`, github-HTTPS-hosts (`github.com`,
`.githubusercontent.com`, `codeload.github.com`), `.pypi.org`, `.pythonhosted.org`
en `.npmjs.org`. Verzoeken naar andere domeinen SHALL geweigerd worden.

De proxy SHALL een access-log bijhouden zodat elk uitgaand verzoek achteraf
reconstrueerbaar is.

#### Scenario: Toegestaan domein

- **WHEN** een worker via de proxy `github.com` of `api.anthropic.com` benadert
- **THEN** staat de proxy het verzoek toe en logt het

#### Scenario: Niet-toegestaan domein

- **WHEN** een worker via de proxy een domein buiten de allowlist benadert
- **THEN** weigert de proxy het verzoek en logt de weigering

### Requirement: Image-pulls vallen buiten de pod-policy

De NetworkPolicy en de proxy-allowlist SHALL geen voorziening voor image-pulls
(`ghcr.io`) bevatten, omdat pulls door kubelet/containerd op de node gebeuren en
niet onder de pod-egress vallen.

#### Scenario: Worker-image wordt gepulld

- **WHEN** een node de worker-image van GHCR pullt
- **THEN** verloopt dat buiten de pod-NetworkPolicy en de proxy om
