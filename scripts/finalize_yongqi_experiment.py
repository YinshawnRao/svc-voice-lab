#!/usr/bin/env python3
"""Register the stage20 chorus deliverables after validation succeeds."""
import json
import random
import shutil

from common import ROOT
from download import hash_file
from run_seven_experiment import dump
from run_yongqi_experiment import EVIDENCE, load


def main():
    c = load('yongqi')
    v = json.loads((EVIDENCE/'final-validation.json').read_text())
    assert c['status']=='POC_PASSED' and v['status']=='PASSED'
    assert v['distinct_conversions']==6 and v['final_audio_files']==12
    keys = [a['key'] for a in c['artists']]
    sample = random.Random(c['seed']).sample(keys, 5)
    c['audition_sample'] = {'seed': c['seed'], 'artist_keys': sample, 'human_audition': False}
    text = json.dumps(c, ensure_ascii=False, indent=2)+'\n'
    (ROOT/'config/experiments/stage20-yongqi.json').write_text(text)
    (ROOT/c['output_directory']/'manifest.json').write_text(text)
    out = c['output_directory']
    before = ROOT/'work/stage20-before-finalize'
    before.mkdir(exist_ok=False)
    backup = []
    for rel in ['README.md','config/status.json','reports/06_summary.md']:
        p = ROOT/rel
        dest = before/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        backup.append({'path':rel,'backup':str(dest.relative_to(ROOT)),
                       'sha256':hash_file(p),'size_bytes':p.stat().st_size})
    dump(EVIDENCE/'shared-index-backups.json', backup)

    p = ROOT/'README.md'
    readme = p.read_text()
    marker = '**最新交付：六人《勇气》副歌。**'
    assert marker not in readme
    readme = readme.replace('**最新交付：', '**前轮交付：', 1)
    entry = (marker+f' [统一试听页]({out}/listen.html) · [实验目录]({out}/) · [报告](reports/27_yongqi.md)。'
             +f"完整副歌 {c['duration_seconds']} 秒，6份混音+6份纯人声，30步单版；"
             +'孙燕姿、蔡依林、萧亚轩、张韶涵、杨丞琳、王心凌，排除原唱梁静茹。'
             +'沿用固定15秒参考，原调转换；技术校验通过，待用户试听。\n\n')
    first = readme.find('\n')
    p.write_text(readme[:first+1]+'\n'+entry+readme[first+1:])

    p = ROOT/'config/status.json'
    s = json.loads(p.read_text())
    previous = json.loads(json.dumps({key:s.get(key) for key in ('scope','deliverables','latest_experiment',
        'latest_experiments','listening_page','listening_pages','next','projects')}))
    s.setdefault('previous_experiment_handoffs',[]).append(previous)
    pages = dict(s.get('listening_pages') or {})
    pages['勇气'] = out+'/listen.html'
    s.update(as_of='2026-10-18', scope='六位固定参考音色演唱梁静茹《勇气》完整副歌，30步单版',
        deliverables=[a['deliverables'][mode]['path'] for a in c['artists'] for mode in ('mix','dry')],
        latest_experiment='config/experiments/stage20-yongqi.json',
        latest_experiments=['config/experiments/stage20-yongqi.json'], active_experiment=None,
        listening_page=out+'/listen.html', listening_pages=pages,
        next=['用户试听六位《勇气》副歌；技术校验不代表听感认可'],
        manual_items=['试听音色、咬字和高音','如需CER，提供独立校对歌词'])
    s['projects']['seed-vc'] = 'POC_PASSED; Courage six singers, 30 steps; human audition pending'
    dump(p, s)

    p = ROOT/'reports/06_summary.md'
    summary = p.read_text()
    summary = summary.replace('## 最新：', '## 前轮：', 1)
    p.write_text('## 最新：六人《勇气》完整副歌\n\n'
        +f"[统一试听](../{out}/listen.html)；副歌{c['duration_seconds']}秒，6份混音+6份纯人声，30步单版。\n\n"
        +'排除原唱梁静茹，六份固定参考与原区间及SHA256均核验；保留原调，重模型串行离线运行。'
        +'技术校验通过，人工试听待办。旧实验保留。[详细报告](27_yongqi.md)。\n\n'+summary)

    p = ROOT/'reports/27_yongqi.md'
    report = p.read_text()
    assert '## 最终验证' not in report
    names = '、'.join(next(a['artist'] for a in c['artists'] if a['key']==key) for key in sample)
    rows = ['', '## 最终验证', '',
        f"{v['protected_files_unchanged']}个既有音频、参考、历史配置和 data/source 全曲的大小与SHA256不变。.DS_Store 未纳入这份对比。",
        f"{v['execution_wrappers_unchanged']}份生成依赖哈希不变。未启用可选F0修复；4秒30步技术冒烟通过。",
        '6个独立转换、12份根目录成品、20条本地试听音轨。源区间、参考、随机种子、单版30步与输入输出哈希均通过校验。',
        '采样率、声道、有限值、非静音、时长及混音峰值检查通过；Node mock DOM同进度切换/参考返回/重新播放通过。此项不是浏览器或人工听音验收。',
        f"生成与评测耗时{c['batch_elapsed_seconds']:.3f}秒；准备、分离、ASR、冒烟另见 reports/27_preparation.md。",
        f"空余空间{v['disk_free_bytes']:,} bytes；累计计费下载{v['download_budget']['charged']:,} bytes，预留{v['download_budget']['reserved']:,} bytes。",
        '滚石官方MV已下载，因副歌内夹有对白未用于转换。歌词版GET返回403且传输0字节。正式源是240秒上传，见准备报告。',
        '固定种子抽5位待试听：'+names+'；试听页同时提供全部6位。',
        '干声测量峰值到1.0，满幅样本比例见下表。这是波形测量，不是听感结论。',
        '没有人工听感认可。各参考候选不足10分钟，使用15秒零样本参考，不训练；自动筛选不能证明无混响/和声/伴奏残留。CER=N/A。', '',
        '| 歌手 | 模式 | 时长/s | 绝对峰值 | >=0.999样本比例 |','|---|---|---:|---:|---:|']
    for row in v['audio']:
        if row['mode']=='reference':
            continue
        rows.append(f"| {row['artist']} | {row['mode']} | {row['duration']:.6f} | {row['peak']:.6f} | {row['near_full_scale_fraction']:.6%} |")
    rows += ['', '干声比混音短约1毫秒，混音按原片段补齐尾部。',
             '仅本机个人实验，没有上传音频、公开发布、commit或push。共享索引更新前保存其最新备份。']
    p.write_text(report+'\n'.join(rows)+'\n')
    print(ROOT/out/'listen.html')


if __name__=='__main__':
    main()
