#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Tests voor habitat_report.py (stdlib-only):
1. diff_hash dekt alleen de agent-code, reproduceerbaar vanaf de branch; exact de
   run-artefacten uitgesloten (geen .habitat/-smokkelkanaal).
2. run-output-<id>.md wordt ALTIJD geschreven (ook zonder result -> placeholder)
   en klobbert een agent-versie (N1).
3. een beschadigde audit.jsonl-regel is fail-closed: geen crash, prev_hash leeg (N3).
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from habitat_report import artifact_excludes, agent_result  # noqa: E402

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


def init_repo(repo):
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    (repo / "README.md").write_text("base\n")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "base")
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def run_report(repo, base, output_file=None, run_id=RUN_ID):
    cmd = [sys.executable, str(HERE / "habitat_report.py"),
           "--repo-dir", str(repo), "--role", "builder",
           "--change", "add-greeting", "--run-id", run_id,
           "--verdict", "ok", "--base-ref", base]
    if output_file is not None:
        cmd += ["--output-file", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def test_diff_hash_reproducible():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        base = init_repo(repo)

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
                    f".habitat/run-output-{RUN_ID}.md", "run-report.json"):
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


def test_run_output_always_written():
    """N1: run-output-<id>.md wordt altijd geschreven, klobbert een agent-versie,
    en valt (per exacte naam) buiten de diff_hash."""
    outfile = Path(".habitat") / f"run-output-{RUN_ID}.md"

    # (a) met een leesbaar result -> die tekst staat in de markdown. Het
    # claude-output-JSON staat BUITEN de repo (zoals $OUT=/work/... naast /work/repo).
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as od:
        repo = Path(d)
        base = init_repo(repo)
        (repo / "GREETING.md").write_text("hoi\n")
        # de agent probeert een eigen run-output te smokkelen
        (repo / ".habitat").mkdir(exist_ok=True)
        (repo / outfile).write_text("SMOKKEL door agent\n")
        git(repo, "add", "-A")
        env = Path(od) / "claude-output.json"
        env.write_text(json.dumps({"result": "De echte review-tekst.", "is_error": False}))
        run_report(repo, base, output_file=env)
        md = (repo / outfile).read_text()
        assert "De echte review-tekst." in md, md
        assert "SMOKKEL door agent" not in md, "agent-run-output niet geklobberd (N1)!"
        assert md.startswith("# Habitat builder — add-greeting"), md
        # valt buiten de diff_hash
        git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "run")
        rr = json.loads((repo / "run-report.json").read_text())
        branch_diff = diff_text(repo, base, *artifact_excludes(RUN_ID))
        assert sha(branch_diff) == rr["diff_hash"], "run-output beïnvloedt de hash"
        assert f".habitat/run-output-{RUN_ID}.md" not in branch_diff

    # (b) zonder --output-file EN zonder result -> placeholder, tóch geschreven
    for env_content in (None, "niet-eens-json", json.dumps({"is_error": True}),
                        json.dumps(["geen object"])):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as od:
            repo = Path(d)
            base = init_repo(repo)
            (repo / "GREETING.md").write_text("hoi\n")
            git(repo, "add", "-A")
            if env_content is None:
                run_report(repo, base)  # geen --output-file
            else:
                env = Path(od) / "claude-output.json"
                env.write_text(env_content)
                run_report(repo, base, output_file=env)
            md = (repo / outfile).read_text()
            assert "geen agent-result" in md, f"placeholder ontbreekt bij {env_content!r}: {md}"

    print("OK: run-output altijd geschreven (placeholder bij geen result), "
          "agent-versie geklobberd, buiten de diff_hash")


def test_agent_result_robuust():
    """agent_result geeft "" bij ontbrekend/onleesbaar/niet-object/niet-string."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        assert agent_result("") == ""
        assert agent_result(str(p / "bestaat-niet.json")) == ""
        bad = p / "bad.json"; bad.write_text("{niet json")
        assert agent_result(str(bad)) == ""
        arr = p / "arr.json"; arr.write_text("[1,2,3]")
        assert agent_result(str(arr)) == ""
        nul = p / "nul.json"; nul.write_text(json.dumps({"result": None}))
        assert agent_result(str(nul)) == ""
        num = p / "num.json"; num.write_text(json.dumps({"result": 123}))
        assert agent_result(str(num)) == ""
        ok = p / "ok.json"; ok.write_text(json.dumps({"result": "hoi"}))
        assert agent_result(str(ok)) == "hoi"
    print("OK: agent_result robuust tegen ontbrekend/onleesbaar/niet-object JSON")


def test_corrupt_audit_failclosed():
    """N3: een beschadigde laatste audit.jsonl-regel laat het rapport niet crashen;
    prev_hash blijft leeg zodat de keten zichtbaar breekt."""
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        base = init_repo(repo)
        (repo / ".habitat").mkdir(exist_ok=True)
        # een eerdere geldige regel + een door de agent bedorven laatste regel
        good = json.dumps({"run_id": "prev", "entry_hash": "abc123", "prev_hash": ""})
        (repo / ".habitat" / "audit.jsonl").write_text(good + "\n{ kapotte regel\n")
        (repo / "GREETING.md").write_text("hoi\n")
        git(repo, "add", "-A")
        env = repo / "claude-output.json"
        env.write_text(json.dumps({"result": "x"}))
        # mag niet crashen
        run_report(repo, base, output_file=env)
        lines = [json.loads(l) for l in
                 (repo / ".habitat" / "audit.jsonl").read_text().splitlines()
                 if l.strip() and not l.startswith("{ kapotte")]
        new = lines[-1]
        assert new["prev_hash"] == "", \
            f"prev_hash niet leeg bij kapotte laatste regel (fail-closed): {new}"
        # F1: de kapotte regel wordt NIET stil weggelaten maar expliciet als
        # (onleesbare) gebroken rij in het HTML-rapport getoond.
        html = (repo / ".habitat" / f"run-report-{RUN_ID}.html").read_text()
        assert "(onleesbare regel)" in html, \
            "kapotte regel stil weggelaten uit het rapport (F1)"

    # F1-scenario: een agent bederft ÁLLE eerdere regels — ze mogen niet stil
    # verdwijnen zodat alleen de eigen entry als 'valide root' overblijft.
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as od:
        repo = Path(d)
        base = init_repo(repo)
        (repo / ".habitat").mkdir(exist_ok=True)
        (repo / ".habitat" / "audit.jsonl").write_text("{ corrupt A\n[1,2,3]\n")
        (repo / "GREETING.md").write_text("hoi\n")
        git(repo, "add", "-A")
        env = Path(od) / "claude-output.json"; env.write_text(json.dumps({"result": "x"}))
        run_report(repo, base, output_file=env)
        html = (repo / ".habitat" / f"run-report-{RUN_ID}.html").read_text()
        # twee onleesbare regels (JSONDecodeError + niet-object) blijven zichtbaar
        assert html.count("(onleesbare regel)") == 2, \
            "niet alle bedorven regels worden als gebroken getoond (F1)"
    print("OK: kapotte audit.jsonl-regel is fail-closed (geen crash, prev_hash leeg, "
          "gebroken rij zichtbaar)")


def main():
    test_diff_hash_reproducible()
    test_run_output_always_written()
    test_agent_result_robuust()
    test_corrupt_audit_failclosed()
    print("ALLE TESTS OK")


if __name__ == "__main__":
    main()
