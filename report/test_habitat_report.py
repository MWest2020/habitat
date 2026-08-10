#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Test: de diff_hash dekt alleen de agent-code en is reproduceerbaar vanaf de
gecommitte branch. Uitgesloten worden EXACT de habitat-artefacten — niet de hele
.habitat/-map: agent-geschreven code onder .habitat/ blijft in de hash (geen
smokkelkanaal). Stdlib-only."""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from habitat_report import artifact_excludes  # noqa: E402  bron van de exclusie-set

RUN_ID = "t1"


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def diff_text(repo, base, *excludes):
    return subprocess.run(
        ["git", "-C", str(repo), "diff", base, "HEAD", "--", ".", *excludes],
        capture_output=True, text=True, check=True).stdout


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def run_report(repo, base):
    subprocess.run([sys.executable, str(HERE / "habitat_report.py"),
                    "--repo-dir", str(repo), "--role", "builder",
                    "--change", "add-greeting", "--run-id", RUN_ID,
                    "--verdict", "ok", "--base-ref", base],
                   check=True, capture_output=True, text=True)


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

        # agent-codewijziging (staged), zoals bij report-tijd. Inclusief bestanden
        # ONDER .habitat/ die de agent zélf schrijft — dat is code (of een als
        # artefact vermómd bestand), geen habitat-artefact van deze run, en MOET
        # in de hash blijven. De namen mikken bewust op de exclusie-globs.
        (repo / "GREETING.md").write_text("Welkom bij habitat-testrepo.\n")
        (repo / ".habitat").mkdir(exist_ok=True)
        (repo / ".habitat" / "evil.py").write_text("print('smuggled')\n")
        (repo / ".habitat" / "run-report-evil.html").write_text("<script>evil()</script>\n")
        (repo / ".habitat" / "run-output-evil.md").write_text("smuggled note\n")
        (repo / ".habitat" / "run-report-nested").mkdir(exist_ok=True)
        (repo / ".habitat" / "run-report-nested" / "x.html").write_text("nested smuggle\n")
        git(repo, "add", "-A")

        run_report(repo, base)

        rr = json.loads((repo / "run-report.json").read_text())
        report_hash = rr["diff_hash"]
        assert "diff_hash_scope" in rr, "diff_hash_scope ontbreekt in run-report.json"
        # het gedocumenteerde scope-commando bevat de exacte run-id, geen wildcard
        assert f"run-report-{RUN_ID}.html" in rr["diff_hash_scope"], rr["diff_hash_scope"]
        assert "*" not in rr["diff_hash_scope"], "wildcard in diff_hash_scope — smokkelkanaal"

        # commit ALLE artefacten (zoals de worker doet) en reproduceer vanaf de branch
        git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "run")
        branch_diff = diff_text(repo, base, *artifact_excludes(RUN_ID))
        branch_hash = sha(branch_diff)

        assert report_hash == branch_hash, (
            f"diff_hash niet reproduceerbaar vanaf branch:\n"
            f"  report={report_hash}\n  branch={branch_hash}")

        # ANTI-SMOKKEL: alles wat de agent zelf onder .habitat/ schrijft — óók
        # als-artefact-vermomde .html/.md en genest — zit WÉL in de hash-scope.
        for smuggle in (".habitat/evil.py", ".habitat/run-report-evil.html",
                        ".habitat/run-output-evil.md",
                        ".habitat/run-report-nested/x.html"):
            assert smuggle in branch_diff, \
                f"agent-geschreven {smuggle} valt buiten de diff_hash — smokkelkanaal!"

        # Alléén de echte artefacten van deze run vallen buiten de hash.
        for art in (".habitat/audit.jsonl", f".habitat/run-report-{RUN_ID}.html",
                    "run-report.json"):
            assert art not in branch_diff, f"habitat-artefact {art} lekt de hash in"

        # De grove exclusie van de héle .habitat/-map zou de smokkelbestanden laten
        # vallen en een AFWIJKENDE hash geven — bewijst dat de precieze exclusie
        # load-bearing is (regressie t.o.v. round-1/round-2 security-FAILs).
        coarse = diff_text(repo, base, ":(exclude).habitat", ":(exclude)run-report.json")
        assert ".habitat/evil.py" not in coarse, "test-aanname: grove exclusie dropt evil.py"
        assert sha(coarse) != report_hash, \
            "grove exclusie geeft dezelfde hash — precieze exclusie doet niets?"

        # Idem: de wildcard-exclusie uit round-2 (afgekeurd) zou de vermomde
        # .html/.md laten vallen — moet dus óók afwijken van onze exacte hash.
        wildcard = diff_text(repo, base, ":(exclude).habitat/audit.jsonl",
                             ":(exclude).habitat/run-report-*.html",
                             ":(exclude).habitat/run-output-*.md",
                             ":(exclude)run-report.json")
        assert sha(wildcard) != report_hash, \
            "wildcard-exclusie geeft dezelfde hash — exacte run-id doet niets?"

        # controle: kaal (zónder enige exclusie) MOET ook verschillen (de habitat-
        # artefacten zouden anders meetellen).
        naive = diff_text(repo, base)
        assert sha(naive) != report_hash, \
            "kale diff zou gelijk zijn — exclusie doet niets?"

    print("OK: diff_hash reproduceerbaar vanaf branch; artefacten uitgesloten, "
          "agent-code onder .habitat/ blijft gedekt")


if __name__ == "__main__":
    main()
