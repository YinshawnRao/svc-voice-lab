#!/usr/bin/env python3
"""Register the validated stage23 chorus without changing older experiments."""
import datetime as dt
import json
import shutil

from common import ROOT
from download import hash_file
from run_seven_experiment import dump
from run_zhixiangaini_experiment import EVIDENCE, load


def main():
    c = load('zhixiangaini')
    v = json.loads((EVIDENCE / 'final-validation.json').read_text())
    assert c['status'] == 'POC_PASSED' and v['status'] == 'PASSED'
    assert v['distinct_conversions'] == 6 and v['final_audio_files'] == 12
    out = c['output_directory']
    for artist in c['artists']:
        for row in artist['deliverables'].values():
            assert hash_file(ROOT / row['path']) == row['sha256']
    before = ROOT / 'work/stage23-before-finalize'
    before.mkdir(exist_ok=False)
    backups = []
    shared = ['README.md', 'config/status.json', 'reports/06_summary.md',
              'reports/30_zhixiangaini.md']
    for rel in shared:
        p = ROOT / rel
        dest = before / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        backups.append({'path': rel, 'backup': str(dest.relative_to(ROOT)),
                        'sha256': hash_file(p), 'size_bytes': p.stat().st_size})
    dump(EVIDENCE / 'shared-index-backups.json', backups)

    p = ROOT / 'README.md'
    text = p.read_text()
    marker = '**最新交付：六人《只想爱你》副歌。**'
    assert marker not in text
    text = text.replace('**最新交付：', '**前轮交付：', 1)
    entry = (marker + f' [统一试听页]({out}/listen.html) · [实验目录]({out}/)'
             + ' · [报告](reports/30_zhixiangaini.md)。'
             + f"完整副歌 {c['duration_seconds']} 秒，6份混音+6份纯人声，30步单版；"
             + '孙燕姿、蔡依林、萧亚轩、梁静茹、张韶涵、王心凌，排除原唱杨丞琳。'
             + '沿用固定15秒参考，原调转换；技术校验通过，待用户试听。\n\n')
    first = text.find('\n')
    p.write_text(text[:first + 1] + '\n' + entry + text[first + 1:])

    p = ROOT / 'config/status.json'
    s = json.loads(p.read_text())
    previous = {key: s.get(key) for key in (
        'scope', 'deliverables', 'latest_experiment', 'latest_experiments',
        'listening_page', 'listening_pages', 'next', 'projects')}
    # Deep copy before modifying the current projects dictionary.
    s.setdefault('previous_experiment_handoffs', []).append(
        json.loads(json.dumps(previous)))
    s.update(
        as_of=dt.datetime.now().date().isoformat(),
        scope='六位固定参考音色演唱杨丞琳《只想爱你》完整副歌，30步单版',
        deliverables=[a['deliverables'][mode]['path']
                      for a in c['artists'] for mode in ('mix', 'dry')],
        latest_experiment='config/experiments/stage23-zhixiangaini.json',
        latest_experiments=['config/experiments/stage23-zhixiangaini.json'],
        listening_page=out + '/listen.html',
        listening_pages={'只想爱你': out + '/listen.html'},
        next=['用户试听六位《只想爱你》副歌；技术校验不代表听感认可'],
        manual_items=['试听音色、咬字和高音', '如需CER，提供独立校对歌词'])
    if s.get('active_experiment') in (None, c['id'],
                                     'config/experiments/stage23-zhixiangaini.json'):
        s['active_experiment'] = None
    s['projects']['seed-vc'] = 'POC_PASSED; six singers, 30 steps; human audition pending'
    dump(p, s)

    p = ROOT / 'reports/06_summary.md'
    text = p.read_text().replace('## 最新：', '## 前轮：', 1)
    p.write_text('## 最新：六人《只想爱你》完整副歌\n\n'
                 + f"[统一试听](../{out}/listen.html)；副歌{c['duration_seconds']}秒，"
                 + '6份混音+6份纯人声，30步单版。\n\n'
                 + '排除原唱杨丞琳，六份固定参考与原区间及SHA256均核验；'
                 + '保留原调，重模型串行离线运行。技术校验通过，人工试听待办。'
                 + '旧实验保留。[详细报告](30_zhixiangaini.md)。\n\n' + text)

    names = '、'.join(next(a['artist'] for a in c['artists'] if a['key'] == key)
                     for key in c['audition_sample']['artist_keys'])
    rows = [
        '', '## 最终验证', '',
        f"技术校验通过。{v['protected_files_unchanged']} 个历史文件大小与 SHA256 不变。",
        f"{v['execution_wrappers_verified']} 份执行脚本哈希核验通过。4 秒 30 步技术冒烟通过。",
        '6 个独立转换、12 份根目录成品、20 条本地试听音轨；参考、源区间、随机种子和参数通过校验。',
        '采样率、声道、有限值、非静音、时长和混音峰值检查通过。'
        'Node mock DOM 同进度切换、参考返回和重新播放通过；这不是浏览器或人工听音验收。',
        f"批次开始/完成 UTC：{c['started_at']} → {c['completed_at']}；"
        '本地执行跨 2026-10-20/21 午夜。',
        f"生成与评测批次耗时 {c['batch_elapsed_seconds']:.3f} 秒。准备与分离另见 30_preparation.md。",
        f"空余空间 {v['disk_free_bytes']:,} bytes；"
        f"累计计费下载 {v['download_budget']['charged']:,} bytes，"
        f"预留 {v['download_budget']['reserved']:,} bytes。",
        '原唱取自索尼音乐中国 B 站 MV；媒体许可证 unknown。'
        '六份参考为固定 15 秒，不训练；候选干净人声不足 10 分钟。'
        '分离结果仍需人工检查混响、和声及伴奏残留。CER=N/A。',
        '固定种子抽 5 位待试听：' + names + '；试听页提供全部六位。',
        '', '| 歌手 | 模式 | 时长/s | 绝对峰值 | >=0.999样本比例 |',
        '|---|---|---:|---:|---:|']
    for row in v['audio']:
        if row['mode'] == 'reference':
            continue
        rows.append(f"| {row['artist']} | {row['mode']} | {row['duration']:.6f} | "
                    f"{row['peak']:.6f} | {row['near_full_scale_fraction']:.6%} |")
    rows += ['', '干声保留模型输出，混音按源片段时长保存。峰值是波形测量，'
             '不能代替主观失真判断。没有人工听感认可。',
             '仅本机个人实验，没有上传音频、公开发布、commit 或 push。']
    p = ROOT / 'reports/30_zhixiangaini.md'
    text = p.read_text()
    assert '## 最终验证' not in text
    p.write_text(text + '\n'.join(rows) + '\n')

    dump(EVIDENCE / 'handoff-validation.json', {
        'status': 'PASSED', 'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'experiment': c['id'], 'listening_page': out + '/listen.html',
        'audio_count': 12, 'human_audition': False,
        'files': [{'path': rel, 'sha256': hash_file(ROOT / rel)}
                  for rel in shared + [out + '/listen.html', out + '/manifest.json']]})
    print(ROOT / out / 'listen.html')


if __name__ == '__main__':
    main()
