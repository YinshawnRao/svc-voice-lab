#!/usr/bin/env python3
"""Snapshot official GitHub metadata and small text files, without cloning media."""
import concurrent.futures
import argparse
import datetime as dt
import html
import json
import re
import subprocess
from pathlib import Path
from common import ROOT

OUT = ROOT / "reports/evidence"

def fetch(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(["curl", "--fail", "--silent", "--show-error", "--location",
                        "--max-time", "45", "--max-filesize", "16000000", url], capture_output=True)
    if p.returncode:
        return {"url": url, "error": p.stderr.decode(errors="replace").strip()}
    path.write_bytes(p.stdout)
    return {"url": url, "path": str(path.relative_to(ROOT)), "bytes": len(p.stdout)}

def snapshot(project):
    pid, repo = project["id"], project["repo"]
    base = f"https://github.com/{repo}"
    dest = OUT / pid
    index = fetch(base, OUT / f"{pid}.html")
    result = {**project, "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(), "sources": [index]}
    if "error" in index:
        return result
    page = (ROOT / index["path"]).read_text()
    for key in ("currentOid", "defaultBranch", "stargazerCount"):
        match = re.search(r'"' + key + r'":("[^"]*"|\d+)', page)
        result[key] = json.loads(match.group(1)) if match else None
    result["archived"] = "This repository was archived" in page
    sha = result["currentOid"]
    if not sha:
        return result
    result["sources"].append(fetch(base + "/commit/" + sha, OUT / f"{pid}-commit.html"))
    cp = OUT / f"{pid}-commit.html"
    if cp.exists():
        dates = re.findall(r'"(?:committedDate|authoredDate)":"([^"]+)"', cp.read_text())
        result["commit_dates"] = sorted(set(dates))
    for filename in project["files"]:
        result["sources"].append(fetch(f"https://raw.githubusercontent.com/{repo}/{sha}/{filename}", dest / filename))
    for suffix in ("releases", "issues"):
        result["sources"].append(fetch(base + "/" + suffix, OUT / f"{pid}-{suffix}.html"))
    (dest / "metadata.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(pid, sha, "stars", result["stargazerCount"], "archived", result["archived"], flush=True)
    return result

def main():
    global OUT
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", help="new evidence directory; never overwrite an existing research snapshot")
    args = p.parse_args()
    if args.run_id:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
            raise SystemExit("Invalid run-id")
        OUT = OUT / args.run_id
    if (OUT / "upstream-snapshot.json").exists():
        raise SystemExit("Snapshot exists; use --run-id <new-id> to preserve existing evidence")
    OUT.mkdir(parents=True, exist_ok=True)
    projects = json.loads((ROOT / "config/projects.json").read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(snapshot, projects))
    (OUT / "upstream-snapshot.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")

if __name__ == "__main__":
    main()
