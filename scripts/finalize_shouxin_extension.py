#!/usr/bin/env python3
"""Finalize four new conversions in the existing six-singer listening directory."""
import json
from common import ROOT
from run_seven_experiment import dump
from extend_shouxin_experiment import EVIDENCE, load, NEW


def main():
    c = load('shouxin')
    validation = 'post-relocation-validation.json' if 'output_relocation' in c else 'final-validation.json'
    v = json.loads((EVIDENCE/validation).read_text())
    assert c['status'] == 'POC_PASSED' and v['status'] == 'PASSED'
    assert v['new_conversions'] == 4 and v['final_audio_files'] == 12
    assert v['approved_two_preserved'] and len(c['artists']) == 6
    out = c['output_directory']
    marker = '**最新交付：《手心的太阳》已补齐六位歌手。**'
    p = ROOT/'README.md'
    text = p.read_text()
    if marker not in text:
        old = '**最新交付：萧亚轩、王心凌《手心的太阳》副歌先行试听。**'
        assert old in text
        entry = (marker + f" [统一试听页]({out}/listen.html) · [实验目录]({out}/) · [报告](reports/22_shouxin.md)。"
                 + '新增孙燕姿《我怀念的》、蔡依林《天空》、梁静茹《崇拜》、杨丞琳《雨爱》；'
                 + '已获认可的萧亚轩、王心凌版本逐字节保留。35.5秒完整副歌、30步单版，6份混音+6份纯人声；'
                 + '技术校验通过，新增四位待试听。原唱张韶涵不参与转换。\n\n')
        text = text.replace(old, entry + '**前轮已认可：萧亚轩、王心凌《手心的太阳》副歌先行试听。**', 1)
        text = text.replace('技术校验通过，待用户试听后再决定是否扩展其余四位；原唱张韶涵不参与转换。',
                            '该两人先行阶段已获用户认可，六人结果见上方；原唱张韶涵不参与转换。', 1)
        p.write_text(text)
    p = ROOT/'config/status.json'
    s = json.loads(p.read_text())
    if s.get('latest_experiment') != 'config/experiments/stage15-shouxin.json':
        s['stage14_deliverables'] = s['deliverables']
        s['stage14_experiments'] = s['latest_experiments']
        s['stage14_listening_pages'] = s['listening_pages']
    s.update(as_of='2026-10-18', scope='六位歌手演唱张韶涵《手心的太阳》完整副歌，补齐四位，30步单版',
        deliverables=[a['deliverables'][mode]['path'] for a in c['artists'] for mode in ('mix', 'dry')],
        latest_experiment='config/experiments/stage15-shouxin.json',
        latest_experiments=['config/experiments/stage15-shouxin.json'], active_experiment=None,
        listening_page=out+'/listen.html', listening_pages={'手心的太阳':out+'/listen.html'},
        next=['用户试听新增孙燕姿、蔡依林、梁静茹、杨丞琳版本；原萧亚轩、王心凌已获认可'],
        manual_items=['试听新增四位音色、咬字与高音；技术校验不代替听感', '如需CER，提供独立校对歌词'])
    s['projects']['seed-vc'] = 'POC_PASSED; Shou Xin De Tai Yang six singers, four added; original two user-approved'
    s['shouxin_user_feedback'] = c['authorization']['user_feedback']
    dump(p, s)
    p = ROOT/'reports/06_summary.md'
    text = p.read_text()
    heading = '## 最新：《手心的太阳》六位歌手已补齐'
    if heading not in text:
        text = text.replace('## 最新：《手心的太阳》两人先行试听',
                            '## 前轮：《手心的太阳》两人先行试听（随后获用户认可）', 1)
        p.write_text(heading + '\n\n'
            + f"[统一试听](../{out}/listen.html)；35.5秒完整副歌，6份混音+6份纯人声，30步单版，技术校验通过。\n\n"
            + '新增孙燕姿、蔡依林、梁静茹、杨丞琳，沿用全局固定参考。'
            + '用户已认可的萧亚轩、王心凌音频和原run全部保留；新增四位待试听。'
            + '原唱张韶涵不转换。[详细报告](22_shouxin.md)。\n\n' + text)
    p = ROOT/'reports/22_shouxin.md'
    text = p.read_text().replace('没有人工听感验收；', '新增四位尚无人工听感验收；')
    if '## 最终验证' not in text:
        rows = ['', '## 最终验证', '',
            f"{v['protected_files_unchanged']}个既有数据、成品、历史配置和全局规范文件大小/SHA256不变；5个可更新文件的原件备份完整。",
            '原萧亚轩、王心凌两份演唱、混音和runs逐字节不变。新增4个转换，合计6个独立转换、12个根目录音频文件、20条本地试听音轨。',
            f"{v['execution_wrappers_unchanged']}份原执行脚本哈希不变，未启用F0修复。固定参考、相同源人声、实际参数、时长、采样率、声道、有限值、非静音和混音峰值均通过校验。",
            'Node mock DOM验证同进度切换、参考返回和重新播放；未冒充浏览器或人工听音验收。',
            f"新增四位生成与评测：{c['batch_elapsed_seconds']:.3f}秒；原两位成本不计入此数。",
            f"空间快照{v['checked_at']}：work={v['space_bytes']['work']:,} bytes；outputs={v['space_bytes']['outputs']:,} bytes；空余={v['disk_free_bytes']:,} bytes。",
            f"本轮无下载。累计计费{v['download_budget']['charged']:,} bytes，历史预留{v['download_budget']['reserved']:,} bytes；未新增模型/依赖，未删除、commit、push或发布。", '',
            '| 歌手 | 模式 | 时长/s | 绝对峰值 | >=0.999样本比例 |', '|---|---|---:|---:|---:|']
        for r in v['audio']:
            if r['mode'] != 'reference':
                rows.append(f"| {r['artist']} | {r['mode']} | {r['duration']:.6f} | {r['peak']:.6f} | {r['near_full_scale_fraction']:.6%} |")
        rows += ['', '干声保留模型原输出，峰值不是主观破音判断；混音尾部补齐见各mix收据。',
                 '用户“效果还挺好”的认可仅对应stage14萧亚轩、王心凌；新增四位听感尚未验收。']
        if v.get('shared_ledger_audit'):
            rows += ['', '首次整体校验因并行stage16向共享下载台账追加一条媒体记录而触发保护检查。原jsonl字节前缀不变，Markdown去除新增条目并还原汇总数后与原SHA256一致；本轮未写入下载台账，保留并行追加。证据见concurrent-ledger-audit.json。']
        if 'output_relocation' in c:
            rows += ['', '按用户要求，实验目录改为 `outputs/stage14-seven-shouxindetaiyang/`；seven沿用实验系列命名，本曲实际为六位转换，原唱张韶涵排除。',
                     '全部音频与原runs逐字节迁移。历史run/evaluation/mix收据及stage14配置保留生成时的路径，由 `reports/evidence/stage15/output-relocation.json` 映射到现目录；活动配置、试听页和导航已更新，迁移后再次通过完整校验。']
        text += '\n'.join(rows)+'\n'
    p.write_text(text)
    for a in c['artists']:
        if a['key'] in NEW:
            print(a['artist'], ROOT/a['deliverables']['mix']['path'])
    print('《手心的太阳》补齐完成：新增4份混音+4份纯人声，同目录共六位；原两位保留。')
    print('试听：', ROOT/out/'listen.html')


if __name__ == '__main__':
    main()
