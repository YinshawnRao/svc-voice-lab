#!/usr/bin/env python3
"""Finalize only stage26 artifacts; preserve shared indexes and concurrent WIP."""
import datetime as dt
import json
import math
from pathlib import Path

from common import ROOT
from download import hash_file
from run_zaijianzhongguohai_round2 import EVIDENCE, load, verify_roster


def main():
    c = load('zaijianzhongguohai')
    validation_path = EVIDENCE / 'final-validation.json'
    v = json.loads(validation_path.read_text())
    assert c['status'] == 'POC_PASSED' and v['status'] == 'PASSED'
    assert v['distinct_conversions'] == 7 and v['final_audio_files'] == 14
    assert v['fixed_roster_references_verified'] and not v['human_audition']
    verify_roster(c)
    out = ROOT / c['output_directory']
    assert json.loads((out / 'manifest.json').read_text()) == c
    assert math.isclose(c['source_end_seconds'] - c['source_start_seconds'],
                        c['duration_seconds'], rel_tol=0, abs_tol=1e-9)
    assert c['created_at'] <= c['started_at'] < c['completed_at']
    for row in c['source_reuse']['files']:
        p = ROOT / row['path']
        assert p.stat().st_size == row['size_bytes'] and hash_file(p) == row['sha256']
    for a in c['artists']:
        run = json.loads((out / 'runs' / a['key'] / 'run.json').read_text())
        assert c['started_at'] <= run['started_at'] < c['completed_at']
        assert run['device'] == 'mps' and run['requested_steps'] == [30]
        assert run['upstream_commit'] == '51383efd921027683c89e5348211d93ff12ac2a8'
        assert run['network'] == 'blocked Python internet sockets + offline library flags'
        assert run['target_sha256'] == a['reference_sha256']
        for row in a['deliverables'].values():
            p = ROOT / row['path']
            assert hash_file(p) == row['sha256'] and p.stat().st_size == row['size_bytes']
        for step in ('convert', 'evaluate'):
            e = json.loads((EVIDENCE / (a['run_id'] + '-' + step + '.json')).read_text())
            assert e['returncode'] == 0 and e['offline_flags']
    rows = [
        '', '## 本轮最终核验', '',
        f"7 个独立新转换、14 份成品；同一完整副歌 {c['source_start_seconds']}–"
        f"{c['source_end_seconds']} 秒，实际 {c['duration_seconds']} 秒，30 步单版。",
        f"{v['protected_files_unchanged']} 份初始已有文件的大小与 SHA256 保持不变；"
        f"{v['execution_wrappers_verified']} 份执行脚本哈希已核验，其中 "
        f"{v['execution_wrappers_unchanged']} 份与生成前完全一致。",
        '所有输出均在本轮开始后实际生成，输入参考、源片段、模型版本、种子、'
        'F0 模式与离线状态核验通过；未复制旧 AI 成品。',
        '全部音频通过 SHA256、采样率、声道、有限值、非静音、时长及混音峰值检查。'
        '纯人声保留原模型输出，允许最多一跳 512 样本的长度差；混音为精确 50.9 秒。',
        '23 条本地音轨及链接完整；Node mock DOM 验证歌手同进度切换、参考返回和重新播放。'
        '这不是浏览器实机播放或人工听感验收。',
        f"生成及评测批次耗时：{c['batch_elapsed_seconds']:.3f} 秒；UTC："
        f"{c['started_at']} → {c['completed_at']}。",
        '各人的实际设备、推理时间、MPS 分配/驱动峰值见上表和 runs/<key>/run.json；'
        '统一内存指标不能当作独立显存或相加。准备过程见 [33_preparation.md](33_preparation.md)。',
        '', '| 歌手 | 模式 | 实际秒数 | 绝对峰值 | >=0.999 样本比例 |',
        '|---|---|---:|---:|---:|',
    ]
    for row in v['audio']:
        if row['mode'] == 'reference':
            continue
        rows.append(f"| {row['artist']} | {row['mode']} | {row['duration']:.6f} | "
                    f"{row['peak']:.6f} | {row['near_full_scale_fraction']:.6%} |")
    if v.get('concurrent_updates'):
        rows += ['', '并行工作说明：初始完整快照保持原样。另一项 stage25 实验更新了其配置、'
                 '共享下载 JSONL 台账及派生 Markdown 台账，这三项不计入“字节未变”数量。'
                 '本轮仅观察并保留它们；下载 JSONL 的原始前缀哈希核验不变。'
                 '确切文件、前后哈希和限定范围见 final-validation.json 的 concurrent_updates。']
    if v.get('post_generation_wrapper_revisions'):
        rows += ['', '七人生成结束后，仅调整本轮专用编排脚本的 validate 函数，以单独记录上述'
                 '并行工作；生成、切片、参考检查、冒烟及报告函数的 AST 均未改变。'
                 '生成时脚本原件与修订前后 SHA256 留存在本轮证据目录。底层模型、推理、'
                 '混音和评测代码未修改。']
    sample = '、'.join(next(a['artist'] for a in c['artists'] if a['key'] == key)
                       for key in c['audition_sample']['artist_keys'])
    rows += ['', f'固定 seed {c["audition_sample"]["seed"]} 抽取 5 位供用户试听：{sample}。'
             '试听页同时提供全部七位。未记录人工认可。',
             '本轮没有新下载、音频上传、公开发布、commit 或 push。原历史成品目录缺失情况'
             '已在准备报告记录；现存历史文件保持原样。共享 README/status/summary 索引未修改。']
    report = ROOT / 'reports/33_zaijianzhongguohai_round2.md'
    text = report.read_text()
    assert '## 本轮最终核验' not in text
    report.write_text(text + '\n'.join(rows) + '\n')
    files = [report, ROOT / 'reports/33_preparation.md', out / 'manifest.json',
             out / 'listen.html', validation_path, Path(__file__).resolve()]
    result = {
        'status': 'PASSED', 'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'experiment': c['id'], 'audio_count': 14, 'human_audition': False,
        'new_generation_verified': True, 'listening_page': str((out / 'listen.html').relative_to(ROOT)),
        'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hash_file(p),
                   'size_bytes': p.stat().st_size} for p in files],
    }
    with (EVIDENCE / 'handoff-validation.json').open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(out / 'listen.html')


if __name__ == '__main__':
    main()
