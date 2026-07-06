#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Zet de orchestrator-tmux op: venster 0 = de Claude Code-orchestrator-sessie +
# een statuspane (wachtrij/escalaties). Job-log-panes voeg je op afroep toe.
#   Gebruik: orchestrator/start-tmux.sh
#   Vereist: tmux, kubectl (geconfigureerd), claude. KUBECTL override-baar.
set -euo pipefail

SESSION=${SESSION:-habitat}
KUBECTL=${KUBECTL:-kubectl}
HERE=$(cd "$(dirname "$0")" && pwd)

tmux has-session -t "$SESSION" 2>/dev/null && { echo "sessie '$SESSION' bestaat al — attach met: tmux attach -t $SESSION"; exit 0; }

# Venster 0: de orchestrator draait claude met dit mandaat (orchestrator/CLAUDE.md)
tmux new-session -d -s "$SESSION" -n orchestrator -c "$HERE"
tmux send-keys  -t "$SESSION":orchestrator "claude" C-m

# Statuspane rechts: wachtrij + escalatie-overzicht (Jobs/Pods in namespace agents)
tmux split-window -h -t "$SESSION":orchestrator -c "$HERE"
tmux send-keys  -t "$SESSION":orchestrator.1 \
  "watch -n5 '$KUBECTL -n agents get jobs,pods -o wide'" C-m
tmux select-pane -t "$SESSION":orchestrator.0

cat <<EOF
tmux-sessie '$SESSION' klaar. Attach:  tmux attach -t $SESSION
  pane 0 = orchestrator (claude, mandaat = orchestrator/CLAUDE.md)
  pane 1 = status (wachtrij/escalaties)
Log-pane per Job op afroep:
  tmux split-window -t $SESSION:orchestrator '$KUBECTL -n agents logs -f job/<jobnaam>'
EOF
