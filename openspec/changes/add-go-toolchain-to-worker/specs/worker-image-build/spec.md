## ADDED Requirements

### Requirement: Go-builds in de kooi zijn offline en falen hard op netwerk

De worker-image SHALL een Go-toolchain bevatten, gepind op tag en digest, zodat
de toegestane `go test|build|vet` echt draaien. De image SHALL
`GOTOOLCHAIN=local`, `GOPROXY=off` en `GOFLAGS=-mod=vendor` zetten, zodat een
Go-build uitsluitend uit de `vendor/` van de doelrepo bouwt en elke poging tot
module- of toolchain-download direct faalt. De egress-policy SHALL hiervoor
niet worden verruimd.

#### Scenario: Gevendorde doelrepo bouwt offline

- **WHEN** een builder-run `go build ./...` draait in een doelrepo met `vendor/`
- **THEN** bouwt Go uit `vendor/` zonder enige netwerkverbinding

#### Scenario: Ontbrekende vendor faalt hard

- **WHEN** een builder-run `go build ./...` draait in een Go-doelrepo zonder
  `vendor/`
- **THEN** faalt het commando direct met een Go-foutmelding over vendoring of
  `GOPROXY=off`, in plaats van te hangen op een geweigerde verbinding

#### Scenario: Nieuwere toolchain gevraagd

- **WHEN** de `go.mod` van een doelrepo een nieuwere Go-versie eist dan de image
- **THEN** faalt de build op `GOTOOLCHAIN=local` en downloadt Go niets
