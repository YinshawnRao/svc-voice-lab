#!/usr/bin/env python3
"""Record the completed two-singer pilot; leave expansion pending user feedback."""
import json
from common import ROOT
from run_seven_experiment import dump
from run_shouxin_experiment import EVIDENCE, load


def main():
    c = load('shouxin')
    v = json.loads((EVIDENCE/'final-validation.json').read_text())
    assert c['status'] == 'POC_PASSED' and v['status'] == 'PASSED'
    assert v['distinct_conversions'] == 2 and v['final_audio_files'] == 4
    assert [a['key'] for a in c['artists']] == ['elva', 'cyndi']
    out = c['output_directory']
    marker = '**最新交付：萧亚轩、王心凌《手心的太阳》副歌先行试听。**'
    p = ROOT/'README.md'
    text = p.read_text()
    if marker not in text:
        old = '**最新交付：七人《蒲公英的约定》副歌。**'
        assert old in text
        entry = (marker + f" [统一试听页]({out}/listen.html) · [实验目录]({out}/) · [报告](reports/21_shouxin.md)。"
                 + f"完整副歌 {c['duration_seconds']} 秒，2份混音+2份纯人声，30步单版；"
                 + '萧亚轩参考《错的人》，王心凌参考《我会好好的》，沿用固定15秒片段。'
                 + '技术校验通过，待用户试听后再决定是否扩展其余四位；原唱张韶涵不参与转换。\n\n')
        p.write_text(text.replace(old, entry + '**前轮交付：七人《蒲公英的约定》副歌。**', 1))
    p = ROOT/'config/status.json'
    s = json.loads(p.read_text())
    if s.get('latest_experiment') != 'config/experiments/stage14-shouxin.json':
        s['stage13_deliverables'] = s['deliverables']
        s['stage13_experiments'] = s['latest_experiments']
        s['stage13_listening_pages'] = s['listening_pages']
    s.update(as_of='2026-10-18', scope='萧亚轩、王心凌演唱张韶涵《手心的太阳》完整副歌，30步单版，两人先行',
        deliverables=[a['deliverables'][mode]['path'] for a in c['artists'] for mode in ('mix', 'dry')],
        latest_experiment='config/experiments/stage14-shouxin.json',
        latest_experiments=['config/experiments/stage14-shouxin.json'], active_experiment=None,
        listening_page=out+'/listen.html', listening_pages={'手心的太阳':out+'/listen.html'},
        next=['等待用户试听萧亚轩、王心凌版本后决定是否扩展孙燕姿、蔡依林、梁静茹、杨丞琳；不自动扩展'],
        manual_items=['试听音色、咬字和高音；技术校验不代表听感认可', '如需CER，提供独立校对歌词'])
    s['projects']['seed-vc'] = 'POC_PASSED; Shou Xin De Tai Yang two-singer pilot; human audition and expansion pending'
    dump(p, s)
    p = ROOT/'reports/06_summary.md'
    text = p.read_text()
    heading = '## 最新：《手心的太阳》两人先行试听'
    if heading not in text:
        text = text.replace('## 最新：七人《蒲公英的约定》与固定默认参考',
                            '## 前轮：七人《蒲公英的约定》与固定默认参考', 1)
        p.write_text(heading + '\n\n'
            + f"[统一试听](../{out}/listen.html)；完整副歌{c['duration_seconds']}秒，2份混音+2份纯人声，30步单版，技术校验通过。\n\n"
            + '仅萧亚轩《错的人》与王心凌《我会好好的》两份固定参考，保留原曲音高。'
            + '用户试听后再决定是否扩展另外四位，原唱张韶涵排除；尚无听感认可。'
            + '旧实验保留。[详细报告](21_shouxin.md)。\n\n' + text)
    p = ROOT/'reports/21_shouxin.md'
    text = p.read_text()
    if '## 最终验证' not in text:
        rows = ['', '## 最终验证', '',
            f"{v['protected_files_unchanged']}个既有数据、成品、历史配置和全局规范文件大小及SHA256不变；未删除文件。",
            f"{v['execution_wrappers_unchanged']}份执行脚本哈希不变；未启用F0修复。",
            '2个独立转换、4个根目录成品、8条本地试听音轨；两份参考与冻结阵容配置一致。',
            '输入输出哈希、采样率、声道、有限值、时长、非静音和混音峰值校验通过。Node mock DOM验证同进度切换、参考返回与重新播放；非浏览器或人工听音验收。',
            f"生成与评测批次：{c['batch_elapsed_seconds']:.3f}秒。空间快照{v['checked_at']}：work={v['space_bytes']['work']:,} bytes；outputs={v['space_bytes']['outputs']:,} bytes；空余={v['disk_free_bytes']:,} bytes。",
            f"下载累计计费{v['download_budget']['charged']:,} bytes；历史预留{v['download_budget']['reserved']:,} bytes；未新增模型/依赖，未commit、push或发布。", '',
            '| 歌手 | 模式 | 时长/s | 绝对峰值 | >=0.999样本比例 |', '|---|---|---:|---:|---:|']
        for r in v['audio']:
            if r['mode'] != 'reference':
                rows.append(f"| {r['artist']} | {r['mode']} | {r['duration']:.6f} | {r['peak']:.6f} | {r['near_full_scale_fraction']:.6%} |")
        rows += ['', '干声保留模型原输出，峰值不等于主观破音判断。尾部补齐见各mix收据。',
                 '本轮只完成用户指定的两人先行试听；其余四位等待用户反馈，不属于本轮未完成项。']
        p.write_text(text+'\n'.join(rows)+'\n')
    for a in c['artists']:
        print(a['artist'], ROOT/a['deliverables']['mix']['path'])
    print('《手心的太阳》两人先行完成：2份混音+2份纯人声，技术验证通过，待用户试听。')
    print('试听：', ROOT/out/'listen.html')


if __name__ == '__main__':
    main()
