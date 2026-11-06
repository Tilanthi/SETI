#!/bin/bash
# Self-driving driver for the round-7 completeness campaign.
#
# No agent is attached. It clears orphaned claims left by killed lanes, keeps a
# target number of lanes alive, throttles the large units on free disk so the
# concurrent refit campaign is never starved, and runs `collect` by itself when
# every planned unit has an output. Progress goes to files; nothing is printed
# to a terminal that has to stay connected.
#
# Usage: p90_r7_run.sh [n_small_lanes] [n_big_lanes]
set -u
ROOT=/data/SETI/p90_r7
BIN=/data/SETI/bin
NS=${1:-12}
NB=${2:-3}
SESS=p90r7
LOG=$ROOT/driver.log
export P90R7_ROOT=$ROOT

say() { echo "[$(date -u +%FT%TZ)] $*" >> "$LOG"; }

mkdir -p "$ROOT/lanelogs" "$ROOT/out" "$ROOT/claims" "$ROOT/logs" "$ROOT/injrec"

# --- orphaned claims. A lane that is killed leaves its claim behind and the
# unit is then skipped for ever, which is worse than redoing it.
#
# *** But ONLY when no lane is alive. A claim held by a RUNNING lane is not
# orphaned, and clearing it lets a second lane take the same unit: both then
# do the same work and write the same file. Restarting this driver while its
# lanes were still running did exactly that once.
WLIVE=$(pgrep -c -f "$(printf 'campaign_p90_%s.py work' r7)" || true)
if [ "${WLIVE:-0}" -gt 0 ]; then
  say "skipping orphan sweep: $WLIVE worker processes are alive"
else
python3 - <<'PY' >> "$LOG" 2>&1
import json, os, shutil
ROOT = '/data/SETI/p90_r7'
plan = {u['tag'] for u in json.load(open(ROOT + '/plan.json'))}
n = 0
for t in os.listdir(ROOT + '/claims'):
    if not os.path.exists('%s/out/%s.json' % (ROOT, t)):
        shutil.rmtree('%s/claims/%s' % (ROOT, t), ignore_errors=True)
        shutil.rmtree('%s/work/%s' % (ROOT, t), ignore_errors=True)
        n += 1
print('cleared %d orphaned claims; %d units in plan' % (n, len(plan)))
PY
fi

SMALL=$(cat "$ROOT/small_tags.txt")
BIG=$(cat "$ROOT/big_tags.txt")

tmux has-session -t $SESS 2>/dev/null || tmux new-session -d -s $SESS -n idle "sleep 1000000"

lane() {   # lane <name> <nproc> <floor> <only>
  local n=$1 p=$2 fl=$3 only=$4
  tmux list-windows -t $SESS -F '#{window_name}' | grep -qx "$n" && return 0
  tmux new-window -t $SESS -n "$n" \
    "cd /data/SETI && P90R7_ROOT=$ROOT P90R7_NPROC=$p P90R7_NTONE=${P90R7_LANE_NTONE:-24} \
     P90R7_LADDER=${P90R7_LANE_LADDER:-1.0,1.5,2.0,2.5,3.0,3.5,4.0,5.0,6.0,8.0} \
     P90R7_DISK_FLOOR_GB=$fl \
     P90R7_KEEP_MS_TAGS=A002_X10a341d_Xdc45_spw2,A002_X128b034_X11ca9_spw2 \
     P90R7_ONLY=$only python3 $BIN/campaign_p90_r7.py work \
     >> $ROOT/lanelogs/$n.log 2>&1; sleep 5"
}

say "driver start: ns=$NS nb=$NB free=$(df -BG --output=avail /data | tail -1 | tr -dc 0-9)G"

while true; do
  # ★ The tmux SERVER itself died at 2026-09-26T04:21Z and again at
  # 2026-09-27T04:54Z, both times killing every lane AND this driver.  The
  # session check used to run once, before the loop, so a server death was
  # unrecoverable.  Re-assert it every cycle, and run the driver itself under
  # setsid so it is not in the tmux server's process tree at all.
  tmux has-session -t $SESS 2>/dev/null \
    || tmux new-session -d -s $SESS -n idle "sleep 1000000"

  # reap dead lanes' scratch and release only genuinely orphaned claims;
  # safe with lanes running, unlike the blanket sweep
  say "reap: $(python3 $BIN/p90_r7_reap.py)"
  DONE=$(ls "$ROOT/out" | wc -l)
  PLANN=$(python3 -c "import json;print(len(json.load(open('$ROOT/plan.json'))))")
  LEFT=$(python3 - <<PY
import json, os
p = json.load(open('$ROOT/plan.json'))
print(sum(1 for u in p if not os.path.exists('$ROOT/claims/' + u['tag'])))
PY
)
  FREE=$(df -BG --output=avail /data | tail -1 | tr -dc 0-9)
  W=$(pgrep -c -f "campaign_p90_r7.py work" || true)
  # ★ Count BAD statuses every cycle. A unit that raises is recorded and the
  # lane moves on, so a bug that makes every unit fail looks exactly like a
  # campaign that is merely slow. Two hours were lost to that once.
  BAD=$(python3 - <<'PYB'
import glob, json, collections
c = collections.Counter()
for f in glob.glob('/data/SETI/p90_r7/out/*.json'):
    try:
        c[json.load(open(f)).get('status')] += 1
    except Exception:
        c['unreadable'] += 1
bad = {k: v for k, v in c.items() if k not in ('ok',)}
print(('OK=%d ' % c.get('ok', 0)) + (('BAD ' + repr(bad)) if bad else 'no failures'))
PYB
)
  say "done=$DONE/$PLANN unclaimed=$LEFT workers=$W free=${FREE}G | $BAD"

  if [ "$DONE" -ge "$PLANN" ]; then
    say "all units have output; collecting"
    cd /data/SETI && python3 $BIN/campaign_p90_r7.py collect \
      > "$ROOT/collect.out" 2>&1
    say "collect rc=$? -> $ROOT/p90_r7_result.json"
    date -u +%FT%TZ > "$ROOT/CAMPAIGN_DONE"
    break
  fi

  # Small lanes always. Large lanes only while the volume has real room: one
  # of them holds up to 50 GB of split plus copy, and the refit campaign has
  # priority on /data. If the volume falls anyway -- the refit fetches faster
  # than any gate of ours can react -- YIELD: kill the large lanes and give
  # their transient space straight back.
  for i in $(seq 1 "$NS"); do lane "S$i" 8 45 "$SMALL"; done
  if [ "$FREE" -lt 25 ]; then
    for i in $(seq 1 "$NB"); do tmux kill-window -t "$SESS:G$i" 2>/dev/null; done
    say "yield: free=${FREE}G -> $(python3 $BIN/p90_r7_yield.py)"
  elif [ "$FREE" -ge 70 ]; then
    for i in $(seq 1 "$NB"); do lane "G$i" 12 60 "$BIG"; done
  fi
  sleep 90
done
