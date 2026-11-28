#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Tests for dispatch/job_conditions.py and the wait in dispatch/dispatch.sh.
# Lives in worker/ because verify.yml runs every worker/test-*.sh and the
# factory's token may not edit workflows. No cluster: KUBECTL is a fake that
# answers from a script of Job states.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
D="$HERE/../dispatch"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
fails=0
ok()  { echo "ok   $1"; }
bad() { echo "FAIL $1"; fails=$((fails+1)); }
eq()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (got '$2', want '$3')"; fi; }
out() { python3 "$D/job_conditions.py" outcome "$@"; }

# 1. Conditions: only the True ones, as Type=Reason.
json='{"status":{"conditions":[{"type":"FailureTarget","status":"True","reason":"DeadlineExceeded"},{"type":"Suspended","status":"False","reason":"x"}]}}'
eq "conditions: True ones only" "$(echo "$json" | python3 "$D/job_conditions.py")" "FailureTarget=DeadlineExceeded"
eq "conditions: no JSON is empty" "$(echo 'not json' | python3 "$D/job_conditions.py")" ""

# 2. Outcome.
eq "Complete is complete" "$(out 'SuccessCriteriaMet=CompletionsReached Complete=CompletionsReached')" complete
eq "Failed DeadlineExceeded is timeout" "$(out 'FailureTarget=DeadlineExceeded Failed=DeadlineExceeded')" timeout
eq "Failed other is failed" "$(out 'FailureTarget=BackoffLimitExceeded Failed=BackoffLimitExceeded')" failed:BackoffLimitExceeded
eq "FailureTarget alone is interim" "$(out 'FailureTarget=DeadlineExceeded')" interim
eq "SuccessCriteriaMet alone is interim" "$(out 'SuccessCriteriaMet=CompletionsReached')" interim
eq "nothing is pending" "$(out '')" pending
eq "final: FailureTarget deadline is timeout" "$(out --final 'FailureTarget=DeadlineExceeded')" timeout
eq "final: FailureTarget backoff is failed" "$(out --final 'FailureTarget=BackoffLimitExceeded')" failed:BackoffLimitExceeded
eq "final: SuccessCriteriaMet is complete" "$(out --final 'SuccessCriteriaMet=CompletionsReached')" complete

# 3. dispatch.sh end to end with a fake kubectl. Each `get job` pops the next
#    line of $T/states (the last line repeats); a line is the conditions JSON list.
cat > "$T/kubectl" <<'EOF'
#!/usr/bin/env bash
case " $* " in
  *" apply "*) cat >/dev/null; echo "job.batch/x created" ;;
  *" get job "*)
    n=$(cat "$FAKE/n" 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > "$FAKE/n"
    total=$(wc -l < "$FAKE/states"); [ "$n" -gt "$total" ] && n=$total
    echo "{\"status\":{\"conditions\":$(sed -n "${n}p" "$FAKE/states")}}" ;;
  *" get pods "*) echo Pending ;;
  *" logs "*) echo "[habitat] fake log" ;;
esac
EOF
chmod +x "$T/kubectl"
mkdir -p "$T/bin"; printf '#!/bin/sh\nexit 0\n' > "$T/bin/sleep"; chmod +x "$T/bin/sleep"
run() {  # run <states...>: prints dispatch's exit code and last line
  rm -f "$T/n"; printf '%s\n' "$@" > "$T/states"
  o=$(PATH="$T/bin:$PATH" FAKE="$T" KUBECTL="$T/kubectl" WORKER_IMAGE=img:sha \
      HABITAT_LOGDIR="$T/logs" INTERIM_GRACE=15 ACTIVE_DEADLINE_SECONDS=60 \
      bash "$D/dispatch.sh" builder demo MWest2020/demo 2>&1); rc=$?
  echo "$rc $(echo "$o" | tail -1)"
}
FT='[{"type":"FailureTarget","status":"True","reason":"DeadlineExceeded"}]'
FD='[{"type":"FailureTarget","status":"True","reason":"DeadlineExceeded"},{"type":"Failed","status":"True","reason":"DeadlineExceeded"}]'
OK='[{"type":"SuccessCriteriaMet","status":"True","reason":"CompletionsReached"},{"type":"Complete","status":"True","reason":"CompletionsReached"}]'

r=$(run '[]' "$FT" "$FT" "$FD")
[[ "$r" == "1 "*TIME-OUT* ]] && ok "dispatch: FailureTarget then Failed is TIME-OUT, exit 1" || bad "dispatch: FailureTarget then Failed ($r)"
r=$(run '[]' "$FT")
[[ "$r" == "1 "*TIME-OUT* ]] && ok "dispatch: FailureTarget past the grace is TIME-OUT, exit 1" || bad "dispatch: FailureTarget past the grace ($r)"
[ "$(cat "$T/n")" -le 10 ] && ok "dispatch: the grace ends the wait, not WAIT_MAX" || bad "dispatch: waited $(cat "$T/n") polls"
r=$(run '[]' "$OK")
[[ "$r" == "0 "*AFGEROND* ]] && ok "dispatch: Complete is AFGEROND, exit 0" || bad "dispatch: Complete ($r)"
r=$(run '[]')
[[ "$r" == "2 "*GEEN* ]] && ok "dispatch: no condition at all is still exit 2" || bad "dispatch: no condition ($r)"

[ "$fails" -eq 0 ] && echo "all dispatch-condition tests passed" || { echo "$fails failed"; exit 1; }
