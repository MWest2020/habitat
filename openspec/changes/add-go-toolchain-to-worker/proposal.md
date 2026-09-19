# Change: add-go-toolchain-to-worker

## Why

`go test|build|vet` staan in de builder-allowlist (`worker/settings/builder.json`)
en in `docs/reference/roles.md`, maar de image heeft geen Go. Dezelfde vorm als
het shellcheck-gat dat `add-shellcheck-to-worker` dichtte: toegestaan, afwezig.

Het werd zichtbaar bij Wanderer (Go, `go 1.25.0`): de accountability-change moet
via habitat-runs gebouwd worden, en een builder zonder Go kan niet compileren of
testen. De enige eerdere Wanderer-run was docs-only en liep er daarom nooit
tegenaan.

## What changes

- **`worker/Containerfile`**: `/usr/local/go` uit `golang:1.25.0-bookworm`,
  gepind op tag én digest (zelfde patroon als uv), plus
  `GOTOOLCHAIN=local`, `GOPROXY=off`, `GOFLAGS=-mod=vendor`.
- **`docs/reference/roles.md`**: noot dat Go nu echt in de image zit en dat een
  Go-doelrepo moet vendoren.

## Wat níét verandert: de kooi

De egress-policy (`cage/ciliumnetworkpolicy.yaml`) blijft ongewijzigd — dat is
het punt. Geen `proxy.golang.org`, geen `sum.golang.org`. Go-doelrepo's vendoren
hun modules (`vendor/` in git). De drie env-variabelen maken van elke
onbedoelde netwerk-fetch een harde, leesbare fout in plaats van een time-out
tegen een geweigerde verbinding:

- zonder `GOTOOLCHAIN=local` downloadt Go zelf een nieuwere toolchain zodra een
  `go.mod` er een vraagt — alsnog egress;
- zonder `GOPROXY=off` probeert Go ontbrekende modules op te halen;
- zonder `GOFLAGS=-mod=vendor` negeert Go een aanwezige `vendor/` in sommige
  situaties.

## Versiebeleid

Eén Go-versie in de image, gelijk aan de go-directive van de (nu enige)
Go-doelrepo. Vraagt een doelrepo later een nieuwere versie, dan faalt de build
hard op `GOTOOLCHAIN=local` en is de oplossing een zichtbare pin-bump hier.

## Impact

- Image ~250 MB groter (de Go-distributie). Nieuwe tag; dispatchers verzetten
  `WORKER_IMAGE`.
- Niet-Go-doelrepo's merken niets: de env-variabelen gelden alleen voor `go`.
