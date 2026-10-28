#!/usr/bin/env python3
"""Rebuild validated preparation environments from audited local artifacts only."""
import argparse
import json
import subprocess
import sys
import time
from common import ROOT, local_env
from download import hash_file

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=["seed-vc-core", "seed-vc-cli", "demucs"])
    parser.add_argument("--python", default="/opt/homebrew/bin/python3.10")
    args = parser.parse_args()
    project = "seed-vc" if args.project.startswith("seed-vc-") else args.project
    manifests = ["core-downloads.json", "core-fix-downloads.json"]
    if args.project == "seed-vc-cli":
        manifests = ["seed-vc-cli-downloads.json"]
    if project == "demucs":
        manifests.extend(["demucs-downloads.json", "demucs-fix-downloads.json"])
    for manifest in manifests:
        for item in json.loads((ROOT / "config" / manifest).read_text()):
            path = ROOT / item["dest"]
            if not path.is_file() or path.stat().st_size != item["size_bytes"] or hash_file(path) != item["sha256"]:
                raise SystemExit(f"Missing or unverified artifact: {item['dest']}; fetch via scripts/download.py {manifest}")
    venv = ROOT / ".envs" / project
    if not (venv / "bin/python").exists():
        subprocess.run([args.python, "-m", "venv", str(venv)], check=True)
    python = str(venv / "bin/python")
    lock = ROOT / "config" / f"{args.project}.lock.txt"
    command = [python, "-m", "pip", "install", "--no-index", "--no-build-isolation", "--find-links", str(ROOT / ".cache/wheels")]
    commands = []
    if project == "demucs" or args.project == "seed-vc-cli":
        commands.append(command + ["setuptools==70.3.0", "wheel==0.48.0", "packaging==26.3"])
    preserve_cli = args.project == "seed-vc-core" and (venv / ".svc-cli-ready").exists()
    if not preserve_cli:
        commands.append(command + ["-r", str(lock)])
    commands.append([python, "-m", "pip", "check"])
    if project == "demucs":
        commands.append([python, "-m", "demucs", "--help"])
    elif args.project == "seed-vc-cli":
        commands.append([python, "-c", "import torch, torchaudio, librosa, transformers, dac; print(torch.__version__, torchaudio.__version__, transformers.__version__)"])
    else:
        commands.append([python, str(ROOT / "scripts/mps_probe.py")])
    path = ROOT / "logs" / f"bootstrap-{args.project}-{time.time_ns()}.log"
    with path.open("w") as log:
        for command in commands:
            log.write("COMMAND " + repr(command) + "\n"); log.flush()
            subprocess.run(command, env=local_env(), stdout=log, stderr=subprocess.STDOUT, check=True, cwd=ROOT)
    if args.project == "seed-vc-cli":
        (venv / ".svc-cli-ready").write_text("CLI dependencies checked; model inference must be separately verified.\n")
    print(f"Preparation environment checked; NOT a singing PoC. Log: {path}")

if __name__ == "__main__":
    main()
