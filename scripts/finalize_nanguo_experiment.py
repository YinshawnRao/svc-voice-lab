#!/usr/bin/env python3
"""Register the six local chorus deliverables after their validation succeeds."""
import json
import shutil

from common import ROOT
from download import hash_file
from run_seven_experiment import dump
from run_nanguo_experiment import EVIDENCE, load


def main():
    c = load('nanguo')
    v = json.loads((EVIDENCE/'final-validation.json').read_text())
    assert c['status']=='POC_PASSED' and v['status']=='PASSED'
    assert v['distinct_conversions']==6 and v['final_audio_files']==12
    out = c['output_directory']
    before = ROOT/'work/stage18-before-finalize'
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
    text = p.read_text()
    marker = '**最新交付：六人《我知道你很难过》副歌。**'
    assert marker not in text
    text = text.replace('**最新交付：', '**前轮交付：', 1)
    entry = (marker+f' [统一试听页]({out}/listen.html) · [实验目录]({out}/) · [报告](reports/25_nanguo.md)。'
             +f"完整副歌 {c['duration_seconds']} 秒，6份混音+6份纯人声，30步单版；"
             +'孙燕姿、萧亚轩、梁静茹、张韶涵、杨丞琳、王心凌，排除原唱蔡依林。'
             +'沿用固定15秒参考，原调转换；技术校验通过，待用户试听。\n\n')
    first = text.find('\n')
    p.write_text(text[:first+1]+'\n'+entry+text[first+1:])

    p = ROOT/'config/status.json'
    s = json.loads(p.read_text())
    previous = json.loads(json.dumps({key:s.get(key) for key in ('scope','deliverables','latest_experiment',
        'latest_experiments','listening_page','listening_pages','next','projects')}))
    s.setdefault('previous_experiment_handoffs',[]).append(previous)
    s.update(as_of='2026-10-18',scope='六位固定参考音色演唱蔡依林《我知道你很难过》完整副歌，30步单版',
        deliverables=[a['deliverables'][mode]['path'] for a in c['artists'] for mode in ('mix','dry')],
        latest_experiment='config/experiments/stage18-nanguo.json',
        latest_experiments=['config/experiments/stage18-nanguo.json'],active_experiment=None,
        listening_page=out+'/listen.html',listening_pages={'我知道你很难过':out+'/listen.html'},
        next=['用户试听六位《我知道你很难过》副歌；技术校验不代表听感认可'],
        manual_items=['试听音色、咬字和高音','如需CER，提供独立校对歌词'])
    s['projects']['seed-vc']="POC_PASSED; I Know You're Feeling Blue six singers, 30 steps; human audition pending"
    dump(p,s)

    p = ROOT/'reports/06_summary.md'
    text = p.read_text()
    text = text.replace('## 最新：','## 前轮：',1)
    p.write_text('## 最新：六人《我知道你很难过》完整副歌\n\n'
        +f"[统一试听](../{out}/listen.html)；副歌{c['duration_seconds']}秒，6份混音+6份纯人声，30步单版。\n\n"
        +'排除原唱蔡依林，六份固定参考与原区间及SHA256均核验；保留原调，重模型串行离线运行。'
        +'技术校验通过，人工试听待办。旧实验保留。[详细报告](25_nanguo.md)。\n\n'+text)

    p = ROOT/'reports/25_nanguo.md'
    text = p.read_text()
    assert '## 最终验证' not in text
    names = '、'.join(next(a['artist'] for a in c['artists'] if a['key']==key)
                     for key in c['audition_sample']['artist_keys'])
    rows = ['', '## 最终验证', '',
        f"{v['protected_files_unchanged']}个既有文件大小与SHA256不变。",
        f"{v['execution_wrappers_unchanged']}份共享生成依赖哈希不变，{v['execution_wrappers_verified']}份最终脚本哈希通过校验。未启用可选F0修复；4秒30步技术冒烟通过。",
        '6个独立转换、12份根目录成品、20条本地试听音轨。源区间、参考、随机种子、单版30步与输入输出哈希均通过校验。',
        '采样率、声道、有限值、非静音、时长及混音峰值检查通过；Node mock DOM同进度切换/参考返回/重新播放通过。此项不是浏览器或人工听音验收。',
        f"生成与评测耗时{c['batch_elapsed_seconds']:.3f}秒；准备、排队、分离、ASR、冒烟另见证据。",
        f"空余空间{v['disk_free_bytes']:,} bytes；累计计费下载{v['download_budget']['charged']:,} bytes，预留{v['download_budget']['reserved']:,} bytes。",
        '华纳频道候选经分离人声ASR确认为现场万人合唱，未用于转换；正式源是265秒上传，见 reports/25_preparation.md。',
        '固定种子抽5位待试听：'+names+'；试听页同时提供全部6位。',
        '没有人工听感认可。各参考候选不足10分钟，使用15秒零样本参考，不训练；自动筛选不能证明无混响/和声/伴奏残留。CER=N/A。', '',
        '| 歌手 | 模式 | 时长/s | 绝对峰值 | >=0.999样本比例 |','|---|---|---:|---:|---:|']
    for row in v['audio']:
        if row['mode']=='reference':
            continue
        rows.append(f"| {row['artist']} | {row['mode']} | {row['duration']:.6f} | {row['peak']:.6f} | {row['near_full_scale_fraction']:.6%} |")
    rows += ['', '干声保留模型原输出，峰值不等于主观破音判断；尾部补齐见各mix收据。',
             '仅本机个人实验，没有上传音频、公开发布、commit或push。共享索引更新前保存其最新备份。']
    p.write_text(text+'\n'.join(rows)+'\n')
    print(ROOT/out/'listen.html')


if __name__=='__main__':
    main()
