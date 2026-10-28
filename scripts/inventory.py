#!/usr/bin/env python3
"""Inventory only user-provided audio; never fetch or modify inputs."""
import datetime as dt
import json
import subprocess
from common import ROOT
from download import hash_file

AUDIO = {".wav", ".flac", ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".aiff", ".aif", ".wma"}

def probe(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], capture_output=True, text=True, timeout=60)
    if p.returncode:
        return {"error": p.stderr.strip()}
    data = json.loads(p.stdout)
    audio = next((x for x in data.get("streams", []) if x.get("codec_type") == "audio"), {})
    return {"duration_seconds": float(data.get("format", {}).get("duration", 0)),
            "sample_rate": audio.get("sample_rate"), "channels": audio.get("channels"), "codec": audio.get("codec_name")}

def main():
    result = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(), "target": [], "source": []}
    for kind in ("target", "source"):
        directory = ROOT / "data" / kind
        if not directory.resolve().is_relative_to(ROOT):
            raise SystemExit("External material directory symlink rejected")
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in AUDIO:
                if not path.resolve().is_relative_to(directory.resolve()):
                    result[kind].append({"path": str(path.relative_to(ROOT)), "error": "external symlink rejected"})
                    continue
                result[kind].append({"path": str(path.relative_to(ROOT)), "size_bytes": path.stat().st_size,
                                     "sha256": hash_file(path), **probe(path)})
    result["status"] = "INPUTS_PRESENT_REVIEW_REQUIRED" if all(result[k] for k in ("target", "source")) else "BLOCKED_DATA"
    (ROOT / "reports/evidence/data-inventory.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "target_files": len(result["target"]), "source_files": len(result["source"])}, ensure_ascii=False))

if __name__ == "__main__":
    main()
