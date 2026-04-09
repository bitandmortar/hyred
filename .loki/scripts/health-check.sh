#!/bin/bash
LOKI_ROOT="$(dirname "$0")/.."
STATE="$LOKI_ROOT/state/orchestrator.json"
if [ -f "$STATE" ]; then
  PHASE=$(python3 -c "import json; print(json.load(open('$STATE'))['phase'])" 2>/dev/null || echo "unknown")
  HEALTH=$(python3 -c "import json; print(json.load(open('$STATE')).get('systemHealth','unknown'))" 2>/dev/null || echo "unknown")
  PENDING=$(python3 -c "import json; print(len(json.load(open('$LOKI_ROOT/queue/pending.json'))['tasks']))" 2>/dev/null || echo "?")
  IN_PROG=$(python3 -c "import json; print(len(json.load(open('$LOKI_ROOT/queue/in-progress.json'))['tasks']))" 2>/dev/null || echo "?")
  DONE=$(python3 -c "import json; print(len(json.load(open('$LOKI_ROOT/queue/completed.json'))['tasks']))" 2>/dev/null || echo "?")
  echo "Phase: $PHASE | Health: $HEALTH | Pending: $PENDING | In-Progress: $IN_PROG | Done: $DONE"
else
  echo "ERROR: orchestrator.json not found"
  exit 1
fi
