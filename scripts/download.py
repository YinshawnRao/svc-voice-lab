#!/usr/bin/env python3
"""Audited HTTPS downloader. Limits include failed attempts; no implicit model fetches."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import shutil
import urllib.parse
import urllib.request
from pathlib import Path
from common import ROOT, CONFIG

LEDGER = ROOT / "reports/downloads.jsonl"
RESERVATIONS = ROOT / "reports/download-reservations.json"

def records():
    return [json.loads(x) for x in LEDGER.read_text().splitlines()] if LEDGER.exists() else []

def charged(rows):
    return sum(r.get("budget_bytes", r.get("transferred_bytes", 0)) for r in rows)

def reservations():
    return json.loads(RESERVATIONS.read_text()) if RESERVATIONS.exists() else {}

def save_reservations(data):
    tmp = RESERVATIONS.with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(RESERVATIONS)

def validate(item, used):
    url = urllib.parse.urlparse(item["url"])
    if url.scheme != "https" or url.hostname not in CONFIG["allowed_download_hosts"] or url.username or url.password:
        raise ValueError("unapproved URL")
    if not item.get("license") or not item.get("evidence") or not item.get("purpose"):
        raise ValueError("license/evidence/purpose required; use explicit unknown for unverified license")
    size = item.get("size_bytes")
    if type(size) is not int or size <= 0:
        raise ValueError("unknown or invalid size")
    if size > CONFIG["single_file_limit_bytes"]:
        raise ValueError("single file exceeds 5 GB")
    if used + size > CONFIG["total_download_limit_bytes"]:
        raise ValueError("cumulative download exceeds 30 GB")
    dest = (ROOT / item["dest"]).resolve()
    if not dest.is_relative_to(ROOT.resolve()) or not any(dest.is_relative_to((ROOT / parent).resolve()) for parent in (".cache", "models", "vendor")):
        raise ValueError("destination must be within .cache, models or vendor")
    if item.get("kind") == "model" and not item.get("official_owner_verified"):
        raise ValueError("model requires verified official owner and README evidence")
    return dest

def render():
    rows = records()
    lines = ["# 下载台账", "", "由 `scripts/download.py` / `scripts/media.py` 共用。十进制 GB；失败/部分下载也计入累计流量。",
             "官方 README/许可证等小型调研文本单独保存在 `reports/evidence/`，不计模型/依赖预算。",
             "许可证按来源声明记录；unknown 不代表获得授权。媒体记录公开页面来源，签名流地址与凭据不落盘。", "",
             f"累计已传输：{sum(r.get('transferred_bytes', 0) for r in rows):,} bytes；上限 30,000,000,000 bytes。", "",
             f"预算已计费：{charged(rows):,} bytes（已开始但失败的请求按整文件保守计入）。", "",
             f"未结束下载保守预留：{sum(reservations().values()):,} bytes（进程异常退出也保留，禁止自动清零）。", "",
             "| 文件 | 状态 | 实际下载 bytes | 来源 / 上游依据 | 许可证 | SHA256 |",
             "|---|---|---:|---|---|---|"]
    for r in rows:
        esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
        lines.append("| " + " | ".join(esc(v) for v in (r["dest"], r["status"], r.get("transferred_bytes",0),
            f"[来源]({r['url']}) / [依据]({r['evidence']})", r["license"], r.get("sha256", "N/A"))) + " |")
    (ROOT / "reports/downloads.md").write_text("\n".join(lines) + "\n")

def download(item):
    # Serialize reservations + transfers; a second process cannot overspend the budget.
    lock_path = ROOT / ".cache/download.lock"
    lock_path.parent.mkdir(exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        held = reservations()
        used = charged(records()) + sum(held.values())
        attempt = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        row = {**item, "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
               "transferred_bytes": 0, "status": "SKIPPED"}
        try:
            dest = validate(item, used)
            if dest.exists():
                digest = hash_file(dest)
                if dest.stat().st_size == item["size_bytes"] and item.get("sha256") == digest:
                    print("cached", item["dest"], flush=True)
                    return
                raise ValueError("existing destination not verified; refusing overwrite")
            if shutil.disk_usage(ROOT).free < item["size_bytes"] + CONFIG["minimum_free_disk_bytes"]:
                raise ValueError("insufficient disk reserve")
            dest.parent.mkdir(parents=True, exist_ok=True)
            partial = dest.with_name(dest.name + ".part-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
            row["partial_path"] = str(partial.relative_to(ROOT))
            held[attempt] = item["size_bytes"]
            save_reservations(held)
            request = urllib.request.Request(item["url"], headers={"User-Agent": "svc-voice-lab/1"})
            digest = hashlib.sha256()
            with urllib.request.urlopen(request, timeout=60) as response, partial.open("xb") as f:
                if urllib.parse.urlparse(response.geturl()).scheme != "https":
                    raise ValueError("non-HTTPS redirect")
                declared = response.headers.get("Content-Length")
                if declared and int(declared) != item["size_bytes"]:
                    raise ValueError("server size differs from manifest")
                while True:
                    chunk = response.read(min(1024 * 1024, item["size_bytes"] - row["transferred_bytes"]))
                    if not chunk:
                        break
                    f.write(chunk)
                    digest.update(chunk)
                    row["transferred_bytes"] += len(chunk)
                    if row["transferred_bytes"] == item["size_bytes"]:
                        if not declared:
                            raise ValueError("cannot prove EOF at size boundary without Content-Length")
                        break
            row["sha256"] = digest.hexdigest()
            if row["transferred_bytes"] != item["size_bytes"]:
                raise ValueError("incomplete download")
            if item.get("sha256") and row["sha256"] != item["sha256"]:
                raise ValueError("SHA256 mismatch")
            partial.rename(dest)
            row["status"] = "DOWNLOADED"
        except Exception as e:
            row["error"] = str(e)
            row["status"] = "FAILED" if row["transferred_bytes"] else "SKIPPED"
        row["budget_bytes"] = item["size_bytes"] if attempt in held else 0
        with LEDGER.open("a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        held.pop(attempt, None)
        save_reservations(held)
        render()
        print(row["status"], item["dest"], row.get("error", ""), flush=True)
        if row["status"] != "DOWNLOADED":
            raise RuntimeError(row.get("error", "download failed"))

def hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("manifest", nargs="?")
    args = p.parse_args()
    if not args.manifest:
        render()
        return
    for item in json.loads(Path(args.manifest).read_text()):
        download(item)

if __name__ == "__main__":
    main()
