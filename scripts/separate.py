#!/usr/bin/env python3
"""Run Demucs only with a pre-audited local model repository. Never auto-download."""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from common import ROOT, local_env
from download import hash_file, records
from inventory import AUDIO

def select_songs(targets=None, sources=None):
    """Explicit selections isolate an experiment from other artists in data/."""
    if bool(targets) != bool(sources):
        raise ValueError("Explicit selection requires both --target and --source")
    songs = []
    for kind, selected in (("target", targets), ("source", sources)):
        role_root = (ROOT / "data" / kind).resolve()
        paths = selected if selected else sorted(role_root.rglob("*"))
        for item in paths:
            path = Path(item).resolve()
            if not path.is_relative_to(role_root):
                raise ValueError(f"Input outside data/{kind}: {item}")
            if not path.is_file() or path.suffix.lower() not in AUDIO:
                if selected:
                    raise ValueError(f"Audio file required: {item}")
                continue
            if (kind, path) in songs:
                raise ValueError(f"Duplicate selected input: {item}")
            songs.append((kind, path))
    return songs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-repo", type=Path, required=True)
    parser.add_argument("--model", default="htdemucs")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    parser.add_argument("--target", type=Path, action="append", help="Explicit target file; repeatable, requires --source")
    parser.add_argument("--source", type=Path, action="append", help="Explicit source file; repeatable, requires --target")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        raise SystemExit("Invalid run-id")
    model_repo = args.model_repo.resolve()
    if not model_repo.is_relative_to(ROOT) or not model_repo.is_relative_to((ROOT / "models").resolve()) or not model_repo.is_dir():
        raise SystemExit("BLOCKED_DOWNLOAD: audited local model repo under models/ required")
    approved = {str((ROOT / r["dest"]).resolve()): r for r in records() if r["status"] == "DOWNLOADED" and r.get("kind") == "model"}
    weights = list(model_repo.rglob("*.th"))
    if not weights:
        raise SystemExit("BLOCKED_DOWNLOAD: no model weights")
    # Model YAML files can reference arbitrary components, so audit every file in the local repo.
    for path in model_repo.rglob("*"):
        if path.is_file():
            row = approved.get(str(path.resolve()))
            if not row or row["sha256"] != hash_file(path):
                raise SystemExit(f"BLOCKED_DOWNLOAD: unregistered local model file {path}")
    songs = select_songs(args.target, args.source)
    if not songs:
        raise SystemExit("BLOCKED_DATA: no user audio")
    dest = ROOT / "work" / args.run_id / "separated"
    dest.mkdir(parents=True, exist_ok=False)
    manifest = {"device": args.device, "model": args.model,
                "selection_mode": "explicit" if args.target else "all_data", "songs": []}
    python = ROOT / ".envs/demucs/bin/python"
    start = time.monotonic()
    with (ROOT / "logs" / f"separate-{args.run_id}.log").open("x") as log:
        for kind, song in songs:
            if not song.resolve().is_relative_to((ROOT / "data" / kind).resolve()):
                raise SystemExit("External audio symlink rejected")
            digest = hash_file(song)
            output = dest / kind / digest[:12]
            if output.exists():
                raise SystemExit("Duplicate input hash; refusing output overwrite")
            command = [str(python), "-m", "demucs", "--repo", str(model_repo), "-n", args.model,
                       "--two-stems", "vocals", "-d", args.device, "--shifts", "1", "--overlap", "0.25",
                       "--segment", "7", "--float32", "-j", "1", "-o", str(output), str(song)]
            log.write("COMMAND " + repr(command) + "\n"); log.flush()
            subprocess.run(command, check=True, env=local_env(), stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
            manifest["songs"].append({"source": str(song.relative_to(ROOT)), "sha256": digest,
                                      "output_directory": str(output.relative_to(ROOT)), "command": command})
    manifest["elapsed_seconds"] = time.monotonic() - start
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(dest)

if __name__ == "__main__":
    main()
