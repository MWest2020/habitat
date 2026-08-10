#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Test: de diff_hash dekt alleen de agent-code en is reproduceerbaar vanaf de
gecommitte branch (habitat-artefacten uitgesloten). Stdlib-only."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def diff_hash_from_branch(repo, base):
    # Zoals een auditor het vanaf de branch reproduceert.
    out = subprocess.run(
        ["git", "-C", str(repo), "diff", base, "HEAD", "--", ".",
         ":(exclude).habitat", ":(exclude)run-report.json"],
        capture_output=True, text=True, check=True).stdout
    import hashlib
    return hashlib.sha256(out.encode()).hexdigest()


def main():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@t")
        git(repo, "config", "user.name", "t")
        (repo / "README.md").write_text("base\n")
        git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "base")
        base = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()

        # agent-codewijziging (staged), zoals bij report-tijd
        (repo / "GREETING.md").write_text("Welkom bij habitat-testrepo.\n")
        git(repo, "add", "-A")

        # draai het echte report-script
        subprocess.run([sys.executable, str(HERE / "habitat_report.py"),
                        "--repo-dir", str(repo), "--role", "builder",
                        "--change", "add-greeting", "--run-id", "t1",
                        "--verdict", "ok", "--base-ref", base],
                       check=True, capture_output=True, text=True)

        rr = json.loads((repo / "run-report.json").read_text())
        report_hash = rr["diff_hash"]
        assert "diff_hash_scope" in rr, "diff_hash_scope ontbreekt in run-report.json"

        # commit ALLE artefacten (zoals de worker doet) en reproduceer vanaf de branch
        git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "run")
        branch_hash = diff_hash_from_branch(repo, base)

        assert report_hash == branch_hash, (
            f"diff_hash niet reproduceerbaar vanaf branch:\n"
            f"  report={report_hash}\n  branch={branch_hash}")

        # controle: kaal (zónder exclusie) MOET verschillen (bewijst dat de
        # artefacten anders zouden meetellen)
        import hashlib
        naive = subprocess.run(["git", "-C", str(repo), "diff", base, "HEAD"],
                               capture_output=True, text=True, check=True).stdout
        assert hashlib.sha256(naive.encode()).hexdigest() != report_hash, \
            "kale diff zou gelijk zijn — exclusie doet niets?"

    print("OK: diff_hash reproduceerbaar vanaf branch, artefacten uitgesloten")


if __name__ == "__main__":
    main()
