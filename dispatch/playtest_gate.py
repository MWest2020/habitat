#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Should the chain run the playtester? (change add-playtester-role)

  playtest_gate.py <owner/repo> <builder-branch>   -> exit 0 = run, 1 = skip

A repository opts in with `.factory/playtest.yml` on the builder branch:
    paths:            # globs; the playtester runs when the change touches one
      - web/**
    serve_dir: web    # or serve_cmd: "npm run preview -- --port {port}"
    viewports: [390x844, 1280x800]
    checks: |         # optional, free text for the role
      Open a game, play one round.
Only `paths` matters here; the role reads the rest itself. For the tests,
PLAYTEST_GATE_CONFIG (a file) and PLAYTEST_GATE_CHANGED (newline-separated
paths) replace the two GitHub calls.
"""
import base64, fnmatch, json, os, re, subprocess, sys


def gh(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[:200])
    return json.loads(out.stdout)


def paths_from(config_text):
    """The `paths:` list, block or flow style; no YAML library needed."""
    globs, inside = [], False
    for line in config_text.splitlines():
        m = re.match(r"^paths:\s*\[(.*)\]\s*$", line)
        if m:
            return [g.strip().strip("'\"") for g in m.group(1).split(",") if g.strip()]
        if re.match(r"^paths:\s*$", line):
            inside = True
            continue
        if inside:
            m = re.match(r"^\s+-\s*(.+?)\s*$", line)
            if m:
                globs.append(m.group(1).strip("'\""))
            elif line.strip() and not line.startswith(" "):
                inside = False
    return globs


def main(repo, branch):
    if os.environ.get("PLAYTEST_GATE_CONFIG") is not None:
        cfg_file = os.environ["PLAYTEST_GATE_CONFIG"]
        config = open(cfg_file).read() if os.path.isfile(cfg_file) else None
        changed = [p for p in os.environ.get("PLAYTEST_GATE_CHANGED", "").splitlines() if p]
    else:
        m = re.search(r"([\w.-]+/[\w.-]+?)(?:\.git)?$", repo)
        if not m:
            print(f"playtest-gate: cannot read owner/repo from '{repo}', skip")
            return 1
        repo = m.group(1)
        try:
            blob = gh(f"repos/{repo}/contents/.factory/playtest.yml?ref={branch}")
            config = base64.b64decode(blob["content"]).decode()
        except RuntimeError as exc:
            if "404" in str(exc) or "Not Found" in str(exc):
                config = None
            else:
                print(f"playtest-gate: config unreadable ({exc}), skip")
                return 1
        if config is None:
            print("playtest-gate: no .factory/playtest.yml, skip")
            return 1
        try:
            default = gh(f"repos/{repo}")["default_branch"]
            files = gh(f"repos/{repo}/compare/{default}...{branch}").get("files", [])
            changed = [f["filename"] for f in files]
        except RuntimeError as exc:
            print(f"playtest-gate: diff unreadable ({exc}); the repo opted in, so run")
            return 0
    if config is None:
        print("playtest-gate: no .factory/playtest.yml, skip")
        return 1
    globs = paths_from(config)
    hits = [p for p in changed if any(fnmatch.fnmatch(p, g) for g in globs)]
    if not hits:
        print(f"playtest-gate: change touches none of {globs}, skip")
        return 1
    print(f"playtest-gate: run ({len(hits)} file(s), e.g. {hits[0]})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: playtest_gate.py <owner/repo> <branch>")
    sys.exit(main(sys.argv[1], sys.argv[2]))
