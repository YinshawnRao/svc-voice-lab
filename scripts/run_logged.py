#!/usr/bin/env python3
"""Run a local command with isolated caches, offline flags, timing and a new log."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from common import ROOT, local_env

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--cwd", type=Path, default=ROOT)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/evidence/stage2")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    evidence=args.evidence_dir.resolve()
    if not evidence.is_relative_to(ROOT / "reports/evidence"):
        raise SystemExit("Evidence must be under reports/evidence")
    evidence.mkdir(parents=True,exist_ok=True)
    if not args.name.replace("-", "").replace("_", "").isalnum():
        raise SystemExit("invalid run name")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    log = ROOT / "logs" / (args.name + ".log")
    env = local_env()
    env.update(OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", PYTHONUNBUFFERED="1")
    start = time.monotonic()
    row = {"command": command, "cwd": str(args.cwd), "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
           "offline_flags": True, "log": str(log.relative_to(ROOT))}
    with log.open("x") as output:
        output.write(json.dumps(row) + "\n"); output.flush()
        try:
            result = subprocess.run(command, cwd=args.cwd, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=args.timeout)
            row["returncode"] = result.returncode
        except subprocess.TimeoutExpired:
            row.update(returncode=124, error="timeout")
    row.update(elapsed_seconds=round(time.monotonic()-start, 3), peak_child_rss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    path = evidence / (args.name + ".json")
    with path.open("x") as output:
        json.dump(row, output, ensure_ascii=False, indent=2); output.write("\n")
    print(json.dumps(row, ensure_ascii=False, indent=2))
    return row["returncode"]

if __name__ == "__main__":
    sys.exit(main())
