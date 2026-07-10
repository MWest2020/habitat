## Tasks

- [x] Entrypoint schrijft `.result` → `.habitat/run-output-<run_id>.md`, ná
      `habitat_report.py`, met `jq -e 'has("result")'`-guard
- [x] `bash -n` + shellcheck clean
- [x] Lokale smoke: markdown-output correct; guard slaat over bij kapotte JSON
- [ ] Mark: push → CI bouwt worker-image (`ghcr.io/mwest2020/habitat-worker:<sha>`)
- [ ] Mark: `WORKER_IMAGE`-pin bijwerken bij de volgende dispatch-ronde
- [ ] Live bevestigen op een echte reviewer-run dat `run-output-<id>.md` verschijnt
