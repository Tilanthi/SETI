#!/bin/bash
# run stack2 exactly as stack6 was run: 4 shards, casa PB, nearest, badweight exclusion; then cat in shard order
cd "$1"; source /data/paper_build/env.sh; export PYTHONDONTWRITEBYTECODE=1
for i in 0 1 2 3; do python3 -B stack2.py --groups groups3.json --windows windows.json --out m$i.jsonl --shard $i/4 --pbmodel casa --exclude badweight.json --mode nearest > mlog$i.txt 2>&1 & done
wait; cat m0.jsonl m1.jsonl m2.jsonl m3.jsonl > stack_result.jsonl; md5sum stack_result.jsonl; wc -l stack_result.jsonl
