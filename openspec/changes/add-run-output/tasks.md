## Tasks

- [x] Entrypoint schrijft `.result` → `.habitat/run-output-<run_id>.md`, ná
      `habitat_report.py`, met `jq -e 'has("result")'`-guard
- [x] `bash -n` + shellcheck clean
- [x] Lokale smoke: markdown-output correct; guard slaat over bij kapotte JSON
- [x] Gepusht naar main (commit 0f82043)
- [x] Worker-image gebouwd + gepusht (`ghcr.io/mwest2020/habitat-worker:0f82043b3fb004b5adfda71df976ce103657728c`),
      fix + report/ geverifieerd in de image
- [x] CI-fix: `worker-image.yml` pusht via `GHCR_PAT` i.p.v. GITHUB_TOKEN (commit 65629ec)
      — lost de `write_package`-denial op het niet-gekoppelde user-package op
- [x] `WORKER_IMAGE`-pin gedocumenteerd op de nieuwe SHA (gebruiken bij volgende dispatch)
- [x] Repo-secret `GHCR_PAT` toegevoegd → CI-build groen; CI pushte
      `ghcr.io/mwest2020/habitat-worker:65629ec2a855e9572f0a905cfffeeb47579fab5e`
- [x] Live bevestigd: reviewer-run op `add-caching` (image `…:65629ec…`) pushte
      `.habitat/run-output-reviewer-add-caching-20260711-214642.md` met de volledige
      review-verdict naar branch `habitat/reviewer/add-caching` (verdict=ok, 15 turns)
