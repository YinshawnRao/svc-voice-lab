#!/usr/bin/env python3
"""Register Stage25 only after current-artifact validation has passed."""
import datetime as dt
import json
import shutil

from common import ROOT
from download import hash_file
from run_seven_experiment import dump
from run_ainibushiliangsantian_experiment import EVIDENCE, load, verify_roster


def main():
    c = load('ainibushiliangsantian')
    v = json.loads((EVIDENCE / 'final-validation.json').read_text())
    verify_roster(c)
    assert c['status'] == 'POC_PASSED' and v['status'] == 'PASSED'
    assert v['distinct_conversions'] == 6 and v['final_audio_files'] == 12
    out = c['output_directory']
    assert json.loads((ROOT / out / 'manifest.json').read_text()) == c
    for a in c['artists']:
        for row in a['deliverables'].values():
            p = ROOT / row['path']
            assert hash_file(p) == row['sha256'] and p.stat().st_size == row['size_bytes']
    shared = ['README.md', 'config/status.json', 'reports/06_summary.md',
              'reports/32_ainibushiliangsantian.md']
    before = ROOT / 'work/stage25-before-finalize'
    before.mkdir(exist_ok=False)
    backups = []
    for rel in shared:
        p = ROOT / rel
        dest = before / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        backups.append(dict(path=rel, backup=str(dest.relative_to(ROOT)),
                            sha256=hash_file(p), size_bytes=p.stat().st_size))
    dump(EVIDENCE / 'shared-index-backups.json', backups)

    song = c['source_song']
    names = '、'.join(a['artist'] for a in c['artists'])
    p = ROOT / 'README.md'
    text = p.read_text()
    marker = f'**最新交付：六人《{song}》副歌。**'
    assert marker not in text
    text = text.replace('**最新交付：', '**前轮交付：', 1)
    entry = (marker + f' [统一试听页]({out}/listen.html) · [实验目录]({out}/)'
             + ' · [报告](reports/32_ainibushiliangsantian.md)。'
             + f"完整副歌 {c['duration_seconds']} 秒，6份混音+6份纯人声，30步单版；"
             + names + '，排除原唱梁静茹。固定15秒参考、原调转换；技术校验通过，待用户试听。\n\n')
    first = text.find('\n')
    p.write_text(text[:first+1] + '\n' + entry + text[first+1:])

    p = ROOT / 'config/status.json'
    s = json.loads(p.read_text())
    fields = ('scope', 'deliverables', 'latest_experiment', 'latest_experiments',
              'listening_page', 'listening_pages', 'next', 'projects')
    previous = json.loads(json.dumps({key: s.get(key) for key in fields}))
    s.setdefault('previous_experiment_handoffs', []).append(previous)
    config = 'config/experiments/stage25-ainibushiliangsantian.json'
    s.update(as_of=dt.datetime.now().date().isoformat(),
             scope=f'六位固定参考音色演唱梁静茹《{song}》完整副歌，30步单版',
             deliverables=[a['deliverables'][mode]['path'] for a in c['artists'] for mode in ('mix', 'dry')],
             latest_experiment=config, latest_experiments=[config],
             listening_page=out+'/listen.html', listening_pages={song:out+'/listen.html'},
             next=[f'用户试听六位《{song}》副歌；技术校验不代表听感认可'],
             manual_items=['试听音色、咬字和高音', '如需CER，提供独立校对歌词'])
    if s.get('active_experiment') in (None, c['id'], config):
        s['active_experiment'] = None
    s['projects']['seed-vc'] = 'POC_PASSED; six singers, 30 steps; human audition pending'
    dump(p, s)

    p = ROOT / 'reports/06_summary.md'
    text = p.read_text().replace('## 最新：', '## 前轮：', 1)
    p.write_text(f'## 最新：六人《{song}》完整副歌\n\n'
                 + f"[统一试听](../{out}/listen.html)；副歌 {c['duration_seconds']} 秒，6份混音+6份纯人声，30步单版。\n\n"
                 + '排除原唱梁静茹，六份固定参考及原区间、SHA256均核验；保留原调，串行离线运行。'
                 + '技术校验通过，人工试听待办。旧实验保留。[详细报告](32_ainibushiliangsantian.md)。\n\n' + text)

    sample = '、'.join(next(a['artist'] for a in c['artists'] if a['key'] == key)
                      for key in c['audition_sample']['artist_keys'])
    rows = ['', '## 最终验证', '',
            f"技术校验通过：{v['protected_files_unchanged']} 个历史文件大小与 SHA256 保持不变；"
            f"{v['execution_wrappers_verified']} 份执行脚本哈希核验通过。",
            '4秒30步技术冒烟通过。6个独立转换、12份根目录成品、20条本地试听音轨；参考、源区间、随机种子和参数通过校验。',
            '采样率、声道、有限值、非静音、时长及混音峰值通过检查。Node mock DOM同进度切换、参考返回和重新播放通过；此项不是浏览器或人工听音验收。',
            f"批次开始/完成 UTC：{c['started_at']} → {c['completed_at']}。",
            f"生成与评测耗时 {c['batch_elapsed_seconds']:.3f} 秒。准备、分离和副歌定位见 32_preparation.md。",
            f"源页面：{c['source_url']}；上传者：{c['source_uploader']}；媒体许可证：{c['source_license']}。",
            f"剩余磁盘 {v['disk_free_bytes']:,} bytes；计费下载 {v['download_budget']['charged']:,} bytes；预留 {v['download_budget']['reserved']:,} bytes。",
            '每份参考15秒，不训练；候选干净人声不足10分钟。分离结果的混响、和声及伴奏残留需人工检查。CER=N/A。',
            '固定种子抽5位待试听：'+sample+'；试听页提供全部六位。', '',
            '| 歌手 | 模式 | 时长/s | 绝对峰值 | >=0.999样本比例 |',
            '|---|---|---:|---:|---:|']
    for row in v['audio']:
        if row['mode'] != 'reference':
            rows.append(f"| {row['artist']} | {row['mode']} | {row['duration']:.6f} | {row['peak']:.6f} | {row['near_full_scale_fraction']:.6%} |")
    rows += ['', '干声保留模型原始输出，混音按共同源片段时长保存。波形测量不代替主观失真判断；未作人工听感认可。',
             '仅本机个人实验，没有上传音频、公开发布、commit或push。']
    p = ROOT / 'reports/32_ainibushiliangsantian.md'
    text = p.read_text()
    assert '## 最终验证' not in text
    p.write_text(text+'\n'.join(rows)+'\n')
    dump(EVIDENCE/'handoff-validation.json', dict(status='PASSED',
         checked_at=dt.datetime.now(dt.timezone.utc).isoformat(), experiment=c['id'],
         listening_page=out+'/listen.html', audio_count=12, human_audition=False,
         files=[dict(path=rel,sha256=hash_file(ROOT/rel))
                for rel in shared+[out+'/listen.html',out+'/manifest.json']]))
    print(ROOT/out/'listen.html')


if __name__ == '__main__':
    main()
