# Tasks: add-go-toolchain-to-worker

## 1. Image
- [x] 1.1 `worker/Containerfile`: `COPY --from=golang:1.25.0-bookworm@sha256:…
      /usr/local/go`, `PATH`, `GOTOOLCHAIN=local`, `GOPROXY=off`,
      `GOFLAGS=-mod=vendor`, met commentaar waarom.

## 2. Documentatie
- [x] 2.1 `docs/reference/roles.md`: Go zit in de image; Go-doelrepo's vendoren.

## 3. Gate
- [x] 3.1 `openspec validate add-go-toolchain-to-worker --strict` groen.
- [x] 3.2 CI groen (verify + image-build). Op 383d8e3: worker-image, verify
      en docs-gates success.

## 4. Uitrol
- [x] 4.1 Image-tag na merge noteren:
      `ghcr.io/mwest2020/habitat-worker:383d8e3a2f2e2aec996322de5349abdc4132642f`.
- [x] 4.2 Bevestigd. In de image zelf nagemeten (2026-09-23, een losse pod
      in `agents`): `go version go1.25.0 linux/amd64`, `GOTOOLCHAIN=local`,
      `GOPROXY=off`, `GOFLAGS=-mod=vendor`. En in gebruik: de accountability-,
      standards-, drie-lagen- en toegankelijkheids-runs van Wanderer
      (2026-09-19 t/m 09-22) bouwden allemaal op deze tag met
      `go build ./...` uit vendor/.
