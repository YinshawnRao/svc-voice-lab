#!/usr/bin/env python3
"""Small terminal handoff. Reads state and files; no model execution or downloads."""
import json
import shutil
from common import ROOT
from download import charged, records, reservations
from inventory import AUDIO

def size(path):
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink()) if path.exists() else 0

def main():
    state = json.loads((ROOT / "config/status.json").read_text())
    print(f"本地歌声实验（记录日期 {state['as_of']}）：{state['scope']}")
    print("跑通项目：" + (", ".join(state.get('poc_passed', [])) or "暂无歌声转换 PoC"))
    print("音视频获取：scripts/media.py 支持搜索、URL 探测、审计下载；实测边界见 reports/07_media_acquisition.md。")
    print("推荐：" + state.get('recommendation', '详见 reports/06_summary.md'))
    for project, status in state['projects'].items():
        print(f"  {project}: {status}")
    for kind in ("target", "source"):
        paths = [p for p in (ROOT / "data" / kind).rglob("*") if p.is_file() and p.suffix.lower() in AUDIO]
        print(f"data/{kind}/: {len(paths)} 个音频")
    for name in state.get('deliverables', []):
        print("成品：" + name + ("" if (ROOT/name).is_file() else " [文件缺失]"))
    if state.get('listening_page'):
        print("试听页：" + str(ROOT/state['listening_page']))
    for name in ("work", "outputs", ".envs", ".cache", "reports"):
        n = size(ROOT / name)
        print(f"{name}/: {n:,} bytes ({n / 1024**2:.2f} MiB)")
    print(f"下载预算已计入：{charged(records()):,}/30,000,000,000 bytes；未结束预留：{sum(reservations().values()):,} bytes")
    print(f"磁盘可用：{shutil.disk_usage(ROOT).free:,} bytes")
    for item in state.get('manual_items', []):
        print("待人工处理：" + item)
    print("详细报告：" + str(ROOT / "reports/06_summary.md"))

if __name__ == "__main__":
    main()
