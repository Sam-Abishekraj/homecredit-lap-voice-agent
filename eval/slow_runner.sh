#!/usr/bin/env bash
# Runs a turn-test list slowly against Groq's free tier: run until the daily token cap, wait for it to refill, resume.
# Usage: eval/slow_runner.sh <version> <model> <key_env> <reasoning> <comma-separated ids> <stop-at "YYYY-MM-DD HH:MM" IST>
# Results append to eval/results/<version>/turns_<model>.jsonl (resume-safe). Stop early with: kill <pid>
set -u
cd "$(dirname "$0")/.."
V=$1; M=$2; K=$3; R=$4; IDS=$5; STOP=$(TZ=Asia/Kolkata date -d "$6" +%s)
PY=${PY:-/workspace/salesagents/.venv/bin/python}
while [ "$(date +%s)" -lt "$STOP" ]; do
  OUT="eval/results/$V/turns_$(basename "$M").jsonl"
  DONE=$( [ -f "$OUT" ] && "$PY" -c "import json,sys;print(len({json.loads(l)['id'] for l in open('$OUT')} & set('$IDS'.split(','))))" || echo 0)
  TOTAL=$(echo "$IDS" | tr ',' '\n' | wc -l)
  echo "$(TZ=Asia/Kolkata date '+%F %T IST') $M: $DONE/$TOTAL done"
  [ "$DONE" -ge "$TOTAL" ] && break
  "$PY" eval/run_turns.py --version "$V" --only "$IDS" --agent-model "$M" --agent-key "$K" --reasoning "$R" --workers 1
  sleep 2400   # ~40 min: the 200K tokens/day cap refills at roughly 8K tokens/hour, about 1.5 tests
done
echo "finished $(TZ=Asia/Kolkata date '+%F %T IST')"
