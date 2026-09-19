# Tasks: add-go-toolchain-to-worker

## 1. Image
- [x] 1.1 `worker/Containerfile`: `COPY --from=golang:1.25.0-bookworm@sha256:…
      /usr/local/go`, `PATH`, `GOTOOLCHAIN=local`, `GOPROXY=off`,
      `GOFLAGS=-mod=vendor`, met commentaar waarom.

## 2. Documentatie
- [x] 2.1 `docs/reference/roles.md`: Go zit in de image; Go-doelrepo's vendoren.

## 3. Gate
- [x] 3.1 `openspec validate add-go-toolchain-to-worker --strict` groen.
- [ ] 3.2 CI groen (verify + image-build).

## 4. Uitrol
- [ ] 4.1 Image-tag na merge noteren.
- [ ] 4.2 Eerste Wanderer-run (accountability run 01) op die tag bevestigt
      `go version go1.25.0` en een groene `go build ./...` uit vendor/.
