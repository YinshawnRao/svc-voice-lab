#!/usr/bin/env python3
"""Update local handoff only after the seven-singer extension passes validation."""
import json
from common import ROOT
from run_seven_experiment import dump
from extend_two_song_experiment import SONGS, EV, load


def main():
    v=json.loads((EV/'final-validation.json').read_text())
    assert v['status']=='PASSED' and v['new_conversions']==10 and v['final_audio_files']==28
    configs=[load(k) for k in SONGS]
    assert all(c['status']=='POC_PASSED' for c in configs)
    p=ROOT/'README.md';text=p.read_text();marker='**最新交付：《心墙》《小幸运》两人先行试听。**'
    assert marker in text
    text=text.replace(marker,'**前轮已认可：《心墙》《小幸运》两人先行试听。**',1)
    line='**最新交付：《心墙》《小幸运》均已补齐七位。** [心墙31.4秒试听](outputs/stage10-xinqiang/listen.html) · [小幸运53.8秒试听](outputs/stage10-xiaoxingyun/listen.html)。'
    line+='原张韶涵/萧亚轩成品保留，新增孙燕姿《我怀念的》、蔡依林《天空》、梁静茹《崇拜》、王心凌《我会好好的》、杨丞琳《雨爱》。'
    line+='每首7份混音+7份纯人声，同歌手两首共用同一参考；30步单版。原四份演唱已获用户认可，新增十份待试听。'
    line+='[准备报告](reports/18_preparation.md) · [心墙报告](reports/18_xinqiang.md) · [小幸运报告](reports/18_xiaoxingyun.md)。\n\n'
    text=text.replace('**前轮已认可：《心墙》',line+'**前轮已认可：《心墙》',1)
    # Keep historical delivery details but remove its now-stale outstanding gate.
    text=text.replace('其余五位明确等待用户试听认可后再做。','该先行阶段现已获用户认可，后续补齐结果见上方最新交付。',1)
    p.write_text(text)
    p=ROOT/'config/status.json';s=json.loads(p.read_text())
    s['stage10_deliverables']=s['deliverables'];s['stage10_experiments']=s['latest_experiments']
    s.update(as_of='2026-10-18',scope='《心墙》《小幸运》各七位，原两位保留、新增五位；30步单版',
        deliverables=[a['deliverables'][mode]['path'] for c in configs for a in c['artists'] for mode in ('mix','dry')],
        latest_experiment='config/experiments/stage11-xinqiang.json',
        latest_experiments=['config/experiments/stage11-'+key+'.json' for key in SONGS],
        listening_page=configs[0]['output_directory']+'/listen.html',
        listening_pages={c['source_song']:c['output_directory']+'/listen.html' for c in configs},
        next=['用户试听新增五位的两首歌；原张韶涵/萧亚轩成品已获本轮用户认可并保留'],
        manual_items=['试听新增十份演唱的音色、咬字和高音','如需CER，提供独立校对歌词'])
    s['projects']['seed-vc']='POC_PASSED; 2 songs x 7 singers, 30 steps; original 4 user approved, new 10 listening pending'
    s.setdefault('user_feedback_history',[]).append(configs[0]['user_feedback']);dump(p,s)
    p=ROOT/'reports/06_summary.md';prior=p.read_text().replace('## 最新：两首歌，两位先行试听','## 前轮：两首歌，两位先行试听（现已获用户认可）',1)
    prior=prior.replace('其余五位未生成，等待明确认可。','此为先行阶段快照；用户随后明确认可，七人补齐结果见上方最新记录。',1)
    p.write_text('## 最新：两首歌均补齐七位\n\n原张韶涵/萧亚轩四份演唱保持原字节；新增五位共十份演唱，20个新音频文件。两目录现各7份混音+7份纯人声，总28个成品。\n\n'
        '[心墙试听](../outputs/stage10-xinqiang/listen.html) · [小幸运试听](../outputs/stage10-xiaoxingyun/listen.html)。参考王心凌本轮改为《我会好好的》；其他指定参考保持一致。原四份获用户认可，新增十份待试听。\n\n'+prior)
    for key,c in zip(SONGS,configs):
        lines=['','## 最终验证','',f"{v['protected_files_unchanged']}个既有数据、输出、历史配置的大小与SHA256不变；原两份manifest和试听页的4个备份哈希验证通过。",
            '每目录7个run、14个最终WAV、23条本地试听音轨。四份已认可演唱原字节保留；新增十份独立转换。跨歌曲参考一致，王心凌新参考与旧《变成陌生人》不同。',
            '采样率、声道、有限值、时长、非静音、混音峰值、输入输出哈希检查通过；Node mock DOM验证同进度切换、参考返回和重新播放。无新增结果的人工听音验收。',
            f"空间快照{v['checked_at']}：work={v['space_bytes']['work']:,} bytes，outputs={v['space_bytes']['outputs']:,} bytes，可用磁盘={v['disk_free_bytes']:,} bytes；未删除文件。",
            f"下载累计计入{v['download_budget']['charged']:,} bytes，保留预留{v['download_budget']['reserved']:,} bytes，低于30GB。无新增模型/依赖；未commit、push或发布。",'',
            '| 新增歌手 | 模式 | 时长/s | 绝对峰值 | >=0.999样本比例 |','|---|---|---:|---:|---:|']
        for r in v['audio']:
            if r['song']==c['source_song'] and r['generation_stage']=='stage11' and r['mode']!='reference':
                lines.append(f"| {r['artist']} | {r['mode']} | {r['duration']:.6f} | {r['peak']:.6f} | {r['near_full_scale_fraction']:.6%} |")
        lines+=['','干声保留模型原始输出；接近满幅的样本比例不证明主观破音。混音采用沿用设置；具体采样补齐记录见各mix收据。']
        p=ROOT/f'reports/18_{key}.md';p.write_text(p.read_text()+'\n'.join(lines)+'\n')
    for c in configs:
        print(c['source_song'],c['duration_seconds'],'秒：')
        for a in c['artists']:
            if a['generation_stage']=='stage11':print(a['artist'],ROOT/a['deliverables']['mix']['path'])
    print('新增10份演唱全部完成；两首各七人，共28个混音/纯人声文件。原四份演唱未改动。')


if __name__=='__main__':main()
