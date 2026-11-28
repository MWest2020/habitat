#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""A Job's conditions and its outcome, for dispatch.sh.

  job_conditions.py < job.json            -> "Type=Reason ..." (conditions that are True)
  job_conditions.py outcome "<conds>"     -> complete | timeout | failed:<reason> | interim | pending
  job_conditions.py outcome --final "<conds>"

Kubernetes >= 1.31 first sets an interim condition, FailureTarget or
SuccessCriteriaMet, and the terminal one, Failed or Complete, only once the pods
are gone. dispatch.sh treated any condition as the end and grepped for "Failed",
which "FailureTarget=DeadlineExceeded" does not contain, so a builder that ran
into its deadline was reported as "no outcome" with exit 2 (wordsworth #541,
2026-11-27; synthetic-long-corpus 2026-11-15; two BackoffLimitExceeded runs on
2026-11-17). `interim` means: wait for the terminal condition. With --final
(dispatch gave up waiting) the interim condition counts as the outcome.
"""
import json
import sys


def conditions(text):
    try:
        d = json.loads(text)
    except Exception:
        return ""
    cs = ((d.get("status") or {}).get("conditions")) or []
    return " ".join("%s=%s" % (c.get("type"), c.get("reason") or "")
                    for c in cs if c.get("status") == "True")


def outcome(conds, final=False):
    seen = dict(c.partition("=")[::2] for c in conds.split() if "=" in c)

    def failed(reason):
        return "timeout" if reason == "DeadlineExceeded" else "failed:" + (reason or "onbekend")

    if "Failed" in seen:
        return failed(seen["Failed"])
    if "Complete" in seen:
        return "complete"
    if "FailureTarget" in seen:
        return failed(seen["FailureTarget"]) if final else "interim"
    if "SuccessCriteriaMet" in seen:
        return "complete" if final else "interim"
    return "pending"


def main(argv):
    if argv[:1] == ["outcome"]:
        final = "--final" in argv[1:]
        rest = [a for a in argv[1:] if a != "--final"]
        print(outcome(rest[0] if rest else "", final))
    else:
        print(conditions(sys.stdin.read()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
