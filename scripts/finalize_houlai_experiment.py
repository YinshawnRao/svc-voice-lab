#!/usr/bin/env python3
"""Publish the local handoff after all seven Hou Lai conversions pass validation."""
import json
from common import ROOT
from run_seven_experiment import dump
from run_houlai_experiment import EVIDENCE, load


def main():
    c = load('houlai')
    v = json.loads((EVIDENCE/'final-validation.json').read_text())
    assert c['status'] == 'POC_PASSED' and v['status'] == 'PASSED'
    assert v['distinct_conversions'] == 7 and v['final_audio_files'] == 14
    out = c['output_directory']
    marker = '**最新交付：七人《后来》副歌。**'
    p = ROOT/'README.md'
    text = p.read_text()
    if marker not in text:
        text = text.replace('**最新交付：《心墙》《小幸运》均已补齐七位。**',
                            '**前轮交付：《心墙》《小幸运》均已补齐七位。**', 1)
        entry = (marker + f" [统一试听页]({out}/listen.html) · [实验目录]({out}/) · [报告](reports/19_houlai.md)。"
                 + f"完整一段副歌 {c['duration_seconds']} 秒，7份混音+7份纯人声；30步单版，全部通过技术校验，待人工试听。"
                 + '沿用心墙/小幸运相同参考片段；七人映射已固定为项目默认，见下方默认参考表。\n\n')
        text = text.replace('**前轮交付：《心墙》', entry+'**前轮交付：《心墙》', 1)
        p.write_text(text)
    p = ROOT/'config/status.json'
    s = json.loads(p.read_text())
    if s.get('latest_experiment') != 'config/experiments/stage12-houlai.json':
        s['stage11_deliverables'] = s['deliverables']
        s['stage11_experiments'] = s['latest_experiments']
        s['stage11_listening_pages'] = s['listening_pages']
    s.update(as_of='2026-10-18', scope='七人固定参考阵容演唱刘若英《后来》副歌，30步单版',
        deliverables=[a['deliverables'][mode]['path'] for a in c['artists'] for mode in ('mix','dry')],
        latest_experiment='config/experiments/stage12-houlai.json',
        latest_experiments=['config/experiments/stage12-houlai.json'],
        active_experiment=None, default_roster='config/default-roster.json',
        listening_page=out+'/listen.html', listening_pages={'后来':out+'/listen.html'},
        next=['用户试听七人的《后来》副歌；后续默认沿用固定七人参考，手动指定优先'],
        manual_items=['试听音色、咬字和高音；技术校验不代表人工认可', '如需CER，提供独立校对歌词'])
    s['projects']['seed-vc'] = 'POC_PASSED; Hou Lai seven singers, 30 steps; human audition pending'
    dump(p,s)
    p = ROOT/'reports/06_summary.md'
    text = p.read_text()
    if '## 最新：七人《后来》与固定默认参考' not in text:
        text = text.replace('## 最新：两首歌均补齐七位','## 前轮：两首歌均补齐七位',1)
        p.write_text('## 最新：七人《后来》与固定默认参考\n\n'
            + f"[统一试听](../{out}/listen.html)；副歌{c['duration_seconds']}秒，7份混音+7份纯人声，30步单版，全部通过技术校验。\n\n"
            + '七人及参考已写入AGENTS.md与config/default-roster.json；现用15秒片段逐字节复用，用户手动指定优先。'
            + '旧实验全部保留，本轮待人工试听。[详细报告](19_houlai.md)。\n\n'+text)
    p = ROOT/'reports/19_houlai.md'
    text = p.read_text()
    if '## 最终验证' not in text:
        rows = ['', '## 最终验证', '',
            f"{v['protected_files_unchanged']}个既有数据、成品和历史实验配置文件大小及SHA256不变；没有删除文件。",
            '7个独立转换、14个根目录成品、23条本地试听音轨；七份参考与全局固定配置及前两首歌一致。',
            '采样率、声道、有限值、时长、非静音、混音峰值、输入输出哈希均通过；Node mock DOM验证同进度切换、参考返回与重新播放，未冒充浏览器或人工听音验收。',
            f"生成与评测：{c['batch_elapsed_seconds']:.3f}秒。空间快照{v['checked_at']}：work={v['space_bytes']['work']:,} bytes；outputs={v['space_bytes']['outputs']:,} bytes；空余={v['disk_free_bytes']:,} bytes。",
            f"下载累计计费{v['download_budget']['charged']:,} bytes；历史预留{v['download_budget']['reserved']:,} bytes，低于30GB。未新增模型/依赖，未commit、push或发布。", '',
            '| 歌手 | 模式 | 时长/s | 绝对峰值 | >=0.999样本比例 |', '|---|---|---:|---:|---:|']
        for r in v['audio']:
            if r['mode'] == 'reference': continue
            rows.append(f"| {r['artist']} | {r['mode']} | {r['duration']:.6f} | {r['peak']:.6f} | {r['near_full_scale_fraction']:.6%} |")
        rows += ['', '干声保留模型输出；峰值指标不等于主观破音判断。尾部补齐见各mix收据。']
        p.write_text(text+'\n'.join(rows)+'\n')
    for a in c['artists']:
        print(a['artist'], ROOT/a['deliverables']['mix']['path'])
    print('七人《后来》完成：7份混音+7份纯人声，30步单版；技术验证通过，等待用户试听。')
    print('固定默认：config/default-roster.json；仅用户手动指定时更改。')
    print('试听：', ROOT/out/'listen.html')


if __name__ == '__main__':
    main()
