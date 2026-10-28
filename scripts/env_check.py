#!/usr/bin/env python3
"""Read-only host probe. Deliberately exclude hardware identifiers."""
import datetime as dt
import json
import platform
import shutil
import subprocess
import time
from common import ROOT

def command(args):
    start = time.monotonic()
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=45)
        return {"command": args, "returncode": p.returncode, "stdout": p.stdout.strip(),
                "stderr": p.stderr.strip(), "elapsed_seconds": round(time.monotonic() - start, 3)}
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {"command": args, "error": str(e)}

def main():
    result = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "platform": platform.platform(), "architecture": platform.machine(),
              "disk": dict(zip(("total", "used", "free"), shutil.disk_usage(ROOT))),
              "probes": []}
    cmds = [["sw_vers"], ["sysctl", "-n", "hw.memsize", "hw.physicalcpu", "hw.logicalcpu"],
            ["system_profiler", "SPDisplaysDataType"], ["python3", "--version"],
            ["/opt/homebrew/bin/python3.10", "--version"], ["/opt/homebrew/bin/python3.12", "--version"],
            ["uv", "--version"], ["conda", "--version"], ["git", "--version"],
            ["ffmpeg", "-version"], ["ffprobe", "-version"]]
    for args in cmds:
        result["probes"].append(command(args))
    path = ROOT / "reports/evidence/environment.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(path)

if __name__ == "__main__":
    main()
