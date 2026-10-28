#!/usr/bin/env python3
"""Slice locally separated target vocals. Does not separate, dereverb, or certify cleanliness."""
import argparse
import json
import random
import re
import subprocess
import time
from pathlib import Path
from common import ROOT, CONFIG, local_env
from download import hash_file
from inventory import probe

def intervals(duration, silence_log, minimum=2.0, maximum=15.0):
    """Complement detected silence, split long regions, drop short tails."""
    silences, start = [], None
    for kind, value in re.findall(r"silence_(start|end):\s*([\d.e+-]+)", silence_log):
        value = max(0.0, min(duration, float(value)))
        if kind == "start":
            start = value
        else:
            silences.append((0.0 if start is None else start, value))
            start = None
    if start is not None:
        silences.append((start, duration))
    cursor, regions = 0.0, []
    for begin, end in sorted(silences):
        if begin > cursor:
            regions.append((cursor, begin))
        cursor = max(cursor, end)
    if cursor < duration:
        regions.append((cursor, duration))
    clips, rejected = [], []
    for begin, end in regions:
        while end - begin > maximum:
            clips.append((begin, begin + maximum))
            begin += maximum
        if end - begin >= minimum:
            clips.append((begin, end))
        elif end > begin:
            rejected.append({"start": begin, "end": end, "reason": "shorter_than_minimum"})
    return clips, rejected

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path, help="directory of separated target WAVs under work/")
    p.add_argument("--run-id", required=True)
    args = p.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.run_id):
        raise SystemExit("Invalid run-id")
    source = args.input.resolve()
    if not source.is_relative_to(ROOT) or not source.is_relative_to((ROOT / "work").resolve()):
        raise SystemExit("Input must be separated target vocals under work/")
    files = sorted(source.rglob("*.wav"))
    if not files:
        raise SystemExit("BLOCKED_DATA: no separated WAV vocals")
    dest = ROOT / "work" / args.run_id / "target-slices"
    dest.mkdir(parents=True, exist_ok=False)
    start_time = time.monotonic()
    manifest = {"config": CONFIG, "files": [], "clips": [], "rejected": [],
                "cleanliness": "UNREVIEWED: silence slicing does not remove accompaniment, harmony or reverb"}
    log_path = ROOT / "logs" / f"slice-{args.run_id}.log"
    with log_path.open("x") as log:
        for src in files:
            if not src.resolve().is_relative_to(source):
                raise SystemExit("External symlink rejected")
            info, digest = probe(src), hash_file(src)
            if "error" in info:
                raise SystemExit(info["error"])
            command = ["ffmpeg", "-nostdin", "-hide_banner", "-i", str(src), "-af",
                       f"silencedetect=noise={CONFIG['silence_db']}dB:d={CONFIG['silence_min_seconds']}", "-f", "null", "-"]
            process = subprocess.run(command, capture_output=True, text=True, check=True, env=local_env())
            log.write("COMMAND " + repr(command) + "\n" + process.stderr); log.flush()
            clips, rejected = intervals(info["duration_seconds"], process.stderr, CONFIG["slice_min_seconds"], CONFIG["slice_max_seconds"])
            manifest["files"].append({"path": str(src.relative_to(ROOT)), "sha256": digest, **info})
            manifest["rejected"].extend({"source": str(src.relative_to(ROOT)), **r} for r in rejected)
            for begin, end in clips:
                output = dest / f"{len(manifest['clips']):05d}_{digest[:10]}.wav"
                cmd = ["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", str(src), "-ss", str(begin), "-t", str(end-begin),
                       "-ar", str(CONFIG["sample_rate"]), "-ac", "1", "-c:a", "pcm_s16le", str(output)]
                log.write("COMMAND " + repr(cmd) + "\n"); log.flush()
                subprocess.run(cmd, check=True, env=local_env(), stdout=log, stderr=log)
                manifest["clips"].append({"source": str(src.relative_to(ROOT)), "start": begin, "end": end,
                                          "path": str(output.relative_to(ROOT)), "sha256": hash_file(output), "cleanliness": "unreviewed"})
    manifest["candidate_seconds"] = sum(c["end"] - c["start"] for c in manifest["clips"])
    manifest["approved_clean_seconds"] = None
    manifest["under_10_minutes"] = manifest["candidate_seconds"] < 600
    manifest["audition_sample"] = random.Random(CONFIG["random_seed"]).sample(manifest["clips"], min(5, len(manifest["clips"])))
    manifest["elapsed_seconds"] = round(time.monotonic() - start_time, 3)
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(dest / "manifest.json")

if __name__ == "__main__":
    main()
